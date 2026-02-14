"""
Pass 1: Editorial Evaluation
Ranks entries by quality (Claude) and flags similarity clusters (embeddings).
You review the bottom of the list and draw the cut line.

Usage:
  python qa1.py outputs/decision-making/book.json

Requires:
  AI_GATEWAY_API_KEY env var
  pip install openai numpy python-dotenv
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel

# Load environment variables
load_dotenv()

console = Console()

# --- Config ---
QUALITY_MODEL = "anthropic/claude-sonnet-4.5"
EMBEDDING_MODEL = "google/text-embedding-005"
SIMILARITY_THRESHOLD = 0.85
RATE_LIMIT_DELAY = 1.0  # seconds between API calls

client = OpenAI(
    api_key=os.getenv("AI_GATEWAY_API_KEY"),
    base_url="https://ai-gateway.vercel.sh/v1",
)


def load_book(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_entry_text(entry: dict) -> str:
    """Extract the full text content from an entry."""
    return entry.get("content", "")


def score_entry(entry: dict, book_title: str, book_descriptor: str) -> dict:
    """Score a single entry using Claude. Returns score (1-10) and rationale."""
    prompt = f"""You are a ruthless editor for a book collection called "{book_title}: {book_descriptor}" published at alexandria.press.

This entry must earn its place. Score it 1-10 where:
- 9-10: Exceptional. Reveals something surprising, deeply useful, or beautifully rendered.
- 7-8: Publishable. Solid, distinctive, worth the reader's time.
- 5-6: Weak. Generic, surface-level, or could be swapped with similar entries unnoticed.
- 1-4: Cut. Adds nothing, rehashes obvious information, or feels like filler.

Evaluate on:
- SUBSTANCE: Does it say something worth reading? Does it go beyond what a Wikipedia summary would give?
- DISTINCTIVENESS: Does it feel like its own entry, or is it interchangeable with generic advice?
- ENGAGEMENT: Would a reader stop here or skip past?

Entry name: {entry["name"]}

Entry content:
{get_entry_text(entry)}

Respond in exactly this JSON format, nothing else:
{{"score": <number 1-10>, "rationale": "<one sentence>"}}"""

    try:
        response = client.chat.completions.create(
            model=QUALITY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        # Parse JSON from response, handling possible markdown wrapping
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(raw)
        
        # Get token usage
        usage = getattr(response, "usage", None)
        total_tokens = usage.total_tokens if usage else 0
        
        return {
            "score": result["score"], 
            "rationale": result["rationale"],
            "tokens": total_tokens
        }
    except Exception as e:
        return {"score": -1, "rationale": f"ERROR: {str(e)}", "tokens": 0}


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings for a list of texts. Batches if needed."""
    # Reduced from 20 to 5 to avoid "input token count is 28916 but the model supports up to 20000"
    batch_size = 5 
    all_embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc=f"Embedding batches (size {batch_size})"):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"  Embedding error on batch {i // batch_size}: {e}")
            # Fill with zeros so indices stay aligned
            all_embeddings.extend([[0.0] * 768] * len(batch))
        time.sleep(RATE_LIMIT_DELAY)

    return np.array(all_embeddings)


def compute_similarity_pairs(
    embeddings: np.ndarray, entries: list[dict], threshold: float
) -> list[dict]:
    """Find pairs of entries above similarity threshold."""
    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    normalized = embeddings / norms
    similarity_matrix = normalized @ normalized.T

    pairs = []
    n = len(entries)
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(similarity_matrix[i][j])
            if sim >= threshold:
                pairs.append(
                    {
                        "entry_a": entries[i]["name"],
                        "entry_a_order": entries[i]["order"],
                        "entry_b": entries[j]["name"],
                        "entry_b_order": entries[j]["order"],
                        "similarity": round(sim, 4),
                    }
                )

    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs


def run_pass1(book_path: str, limit: int = None, max_workers: int = 10):
    print(f"Loading {book_path}...")
    book = load_book(book_path)

    title = book.get("title", "Untitled")
    descriptor = book.get("descriptor", "")
    entries = book.get("entries", [])

    # Filter to entries that have content
    valid_entries = [e for e in entries if e.get("content")]
    if limit:
        print(f"Limiting to first {limit} entries.")
        valid_entries = valid_entries[:limit]
    
    print(f"Found {len(valid_entries)} entries with content in '{title}'")

    # --- Quality Scoring ---
    print(f"\nScoring entries with {QUALITY_MODEL} (workers: {max_workers})...")
    scores = []
    total_tokens = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a future for each entry
        future_to_entry = {
            executor.submit(score_entry, entry, title, descriptor): entry 
            for entry in valid_entries
        }
        
        # Process as they complete
        for future in tqdm(as_completed(future_to_entry), total=len(valid_entries), unit="entry"):
            entry = future_to_entry[future]
            try:
                result = future.result()
                
                token_count = result.get("tokens", 0)
                total_tokens += token_count
                
                scores.append(
                    {
                        "order": entry["order"],
                        "slug": entry["slug"],
                        "name": entry["name"],
                        "section": entry.get("metadata", {}).get("section", ""),
                        "score": result["score"],
                        "rationale": result["rationale"],
                        "tokens": token_count,
                    }
                )
            except Exception as e:
                print(f"\nError processing {entry['name']}: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Sort by score descending
    scores.sort(key=lambda x: x["score"], reverse=True)

    # --- Similarity Detection ---
    print(f"\nComputing embeddings with {EMBEDDING_MODEL}...")
    texts = [get_entry_text(e) for e in valid_entries]
    embeddings = get_embeddings(texts)

    print(f"Finding similar pairs (threshold: {SIMILARITY_THRESHOLD})...")
    similar_pairs = compute_similarity_pairs(
        embeddings, valid_entries, SIMILARITY_THRESHOLD
    )
    print(f"Found {len(similar_pairs)} similar pairs")

    # --- Build Report ---
    # Mark entries that appear in similarity clusters
    similar_entry_names = set()
    for pair in similar_pairs:
        similar_entry_names.add(pair["entry_a"])
        similar_entry_names.add(pair["entry_b"])

    for s in scores:
        s["in_similarity_cluster"] = s["name"] in similar_entry_names

    # Stats
    score_values = [s["score"] for s in scores if s["score"] > 0]
    stats = {
        "total_entries": len(valid_entries),
        "mean_score": round(np.mean(score_values), 2) if score_values else 0,
        "median_score": round(float(np.median(score_values)), 2)
        if score_values
        else 0,
        "min_score": min(score_values) if score_values else 0,
        "max_score": max(score_values) if score_values else 0,
        "similar_pairs_found": len(similar_pairs),
        "entries_in_clusters": len(similar_entry_names),
        "total_tokens": total_tokens,
        "avg_tokens_per_entry": round(total_tokens / len(valid_entries)) if valid_entries else 0,
        "total_time_seconds": round(elapsed_time, 2),
        "avg_time_per_entry": round(elapsed_time / len(valid_entries), 2) if valid_entries else 0,
    }

    report = {
        "book_id": book.get("book_id", ""),
        "title": title,
        "descriptor": descriptor,
        "config": {
            "quality_model": QUALITY_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "similarity_threshold": SIMILARITY_THRESHOLD,
        },
        "stats": stats,
        "ranked_entries": scores,
        "similarity_clusters": similar_pairs,
    }

    # --- Save ---
    output_dir = Path(book_path).parent
    report_path = output_dir / "editorial_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Print Summary ---
    print_rich_report(report)
    print(f"\nFull report saved to: {report_path}")

def print_rich_report(report: dict):
    """Print a rich formatted report to the console."""
    stats = report["stats"]
    title = report.get("title", "Unknown Book")
    
    console.print(f"\n[bold underline]{title} - Editorial Report[/bold underline]\n")

    # Stats Grid
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="magenta")
    grid.add_row("Entries Scored:", str(stats["total_entries"]))
    grid.add_row("Mean Score:", str(stats["mean_score"]))
    grid.add_row("Total Tokens:", f"{stats['total_tokens']:,}")
    grid.add_row("Total Time:", f"{stats['total_time_seconds']}s")
    
    console.print(Panel(grid, title="Statistics", border_style="blue"))
    
    # Ranked Entries Table
    table = Table(title="Entry Rankings", box=box.SIMPLE)
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Score", justify="center", style="bold")
    table.add_column("Entry Name", style="white")
    table.add_column("Rationale", style="dim")
    table.add_column("Tokens", justify="right", style="green")

    for i, entry in enumerate(report["ranked_entries"], 1):
        score = entry["score"]
        if score >= 9:
            score_style = "green"
        elif score >= 7:
            score_style = "yellow"
        else:
            score_style = "red"
            
        name = entry["name"]
        if entry.get("in_similarity_cluster"):
            name = f"{name} [bold red]![/]"

        table.add_row(
            str(i),
            f"[{score_style}]{score}[/{score_style}]",
            name,
            entry["rationale"],
            str(entry.get("tokens", 0))
        )

    console.print(table)

    # Similarity Clusters
    if report["similarity_clusters"]:
        sim_table = Table(title="Similarity Clusters", box=box.ROUNDED, border_style="red")
        sim_table.add_column("Similarity", justify="right", style="bold red")
        sim_table.add_column("Entry A", style="yellow")
        sim_table.add_column("Entry B", style="yellow")
        
        for pair in report["similarity_clusters"]:
            sim_table.add_row(
                f"{pair['similarity']:.2f}",
                pair["entry_a"],
                pair["entry_b"]
            )
        console.print(sim_table)
    else:
        console.print("\n[green]No similarity clusters found.[/green]")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pass 1: Editorial Evaluation")
    parser.add_argument("book_path", help="Path to book.json")
    parser.add_argument("--limit", type=int, help="Limit number of entries to process")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    run_pass1(args.book_path, limit=args.limit, max_workers=args.workers)