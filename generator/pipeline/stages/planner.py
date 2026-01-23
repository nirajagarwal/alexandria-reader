import json
from pathlib import Path
from ..config import PROMPTS_DIR, ENTITIES_DIR
from ..models import Book, Entry
from .base import Stage

class Planner(Stage):
    def execute(self, collection_id: str) -> Book:
        print(f"Planning book: {collection_id}")
        
        # Load entities
        entities_path = ENTITIES_DIR / f"{collection_id}.json"
        if not entities_path.exists():
            raise FileNotFoundError(f"Entities file not found: {entities_path}")
            
        with open(entities_path, "r") as f:
            data = json.load(f)
            
        # Load prompt
        prompt_path = PROMPTS_DIR / f"{collection_id}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            
        with open(prompt_path, "r") as f:
            system_prompt = f.read()
            
        # Create entries
        entries = []
        for item in data.get("entries", []):
            entry = Entry(
                order=item["order"],
                slug=item["slug"],
                name=item["name"],
                descriptor=item.get("descriptor"),
                metadata={k:v for k,v in item.items() if k not in ["order", "slug", "name", "descriptor"]}
            )
            entries.append(entry)
            
        from datetime import datetime
        
        return Book(
            book_id=collection_id,
            title=data.get("title", collection_id),
            descriptor=data.get("descriptor", ""),
            entries=entries,
            system_prompt=system_prompt,
            card_display=data.get("card_display", {}),
            created_at=datetime.now().isoformat()
        )
