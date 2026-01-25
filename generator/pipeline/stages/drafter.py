import anthropic
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import re

from ..config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from ..models import Book, Entry
from .base import Stage

class Drafter(Stage):
    def __init__(self, context):
        super().__init__(context)
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.lock = threading.Lock()

    def execute(self, book: Book) -> Book:
        print(f"Drafting content for {len(book.entries)} entries...")
        
        # Filter entries that need generation
        entries_to_process = []
        for i, entry in enumerate(book.entries):
            if i < self.context.resume_from:
                continue
            
            # Check if file exists on disk to decide skipping
            if self.context.skip_existing:
                from ..config import OUTPUT_DIR
                file_path = OUTPUT_DIR / self.context.collection_id / "entries" / f"{entry.slug}.md"
                
                if file_path.exists():
                    print(f"Skipping (exists): {entry.name}")
                    # Load existing content so subsequent stages (Enricher) have it
                    with open(file_path, "r") as f:
                        entry.content = f.read()
                        entry.descriptor = self._extract_descriptor(entry.content)
                    continue
                
            entries_to_process.append(entry)
            
        print(f"Generating {len(entries_to_process)} entries with {self.context.workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.context.workers) as executor:
            future_to_entry = {
                executor.submit(self._generate_entry, book.system_prompt, entry): entry 
                for entry in entries_to_process
            }
            
            completed = 0
            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    content, usage = future.result()
                    
                    with self.lock:
                        # Ensure content starts with a header
                        if not content.strip().startswith("#"):
                            content = f"# {entry.name}\n\n{content}"
                            
                        entry.content = content
                        entry.generated_at = datetime.now(timezone.utc).isoformat()
                        entry.descriptor = self._extract_descriptor(content)
                        
                        completed += 1
                        self.context.stats["processed"] += 1
                        self.context.stats["tokens_in"] += usage.input_tokens
                        self.context.stats["tokens_out"] += usage.output_tokens
                        
                        print(f"[{completed}/{len(entries_to_process)}] ✓ {entry.name}")
                        
                except Exception as e:
                    with self.lock:
                        entry.error = str(e)
                        self.context.stats["failed"] += 1
                        print(f"✗ {entry.name}: {e}")
        
        return book

    def _generate_entry(self, system_prompt: str, entry: Entry):
        message = self.client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": entry.name}
            ]
        )
        return message.content[0].text, message.usage

    def _extract_descriptor(self, content: str) -> str:
        lines = content.strip().split("\n")
        for line in lines[:5]:
            match = re.match(r"\*\*\*(.+?)\*\*\*", line.strip())
            if match:
                return match.group(1)
        return None
