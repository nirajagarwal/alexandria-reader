#!/usr/bin/env python3
"""
Generate podcast panel discussion scripts from Alexandria Press entries.

Usage:
    python generate_podcast_script.py --collection practices --entry fasting
    python generate_podcast_script.py --collection practices --all
"""

import json
import os
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def load_config():
    """Load podcast configuration."""
    config_path = Path(__file__).parent / "podcast_config.json"
    with open(config_path) as f:
        return json.load(f)


def load_entry(collection: str, entry_slug: str):
    """Load entry content from book.json."""
    book_path = Path(__file__).parent.parent / "outputs" / collection / "book.json"
    
    with open(book_path) as f:
        book_data = json.load(f)
    
    # Find the entry
    for entry in book_data["entries"]:
        if entry["slug"] == entry_slug:
            return {
                "title": entry["name"],
                "content": entry["content"],
                "descriptor": entry.get("descriptor"),
                "collection": collection
            }
    
    raise ValueError(f"Entry '{entry_slug}' not found in {collection}")


def build_script_prompt(entry_data: dict, config: dict):
    """Build the prompt for Claude to generate the script."""
    collection = entry_data["collection"]
    collection_config = config["collections"][collection]
    panelists = collection_config["panelists"]
    guidelines = config["script_guidelines"]
    
    # Build panelist descriptions
    panelist_desc = []
    for p in panelists:
        panelist_desc.append(
            f"- **{p['name']}** ({p['role']}): {p['expertise']}. {p['voice_style']}"
        )
    
    prompt = f"""You are a skilled podcast script writer. Create an engaging {collection_config['target_duration_minutes']}-minute panel discussion script based on the following entry from the "{collection.title()}" collection.

## PANELISTS

{chr(10).join(panelist_desc)}

## SOURCE MATERIAL

Title: {entry_data['title']}

{entry_data['content']}

## SCRIPT REQUIREMENTS

1. **Format**: Use markdown with speaker labels in the format `**SPEAKER_NAME:**`
2. **Duration**: Target {collection_config['target_duration_minutes']} minutes (~{guidelines['word_count_target']} words)
3. **Structure**: 
   - Opening: Moderator introduces topic and panelists (1-2 min)
   - 3-5 thematic segments with clear transitions
   - Closing: Synthesis and key takeaways (1-2 min)

4. **Conversation Style**:
   - Natural back-and-forth dialogue, NOT sequential monologues
   - Panelists respond to and build on each other's points
   - Include moments of agreement, gentle disagreement, and synthesis
   - Use conversational language while maintaining expertise

5. **Content Fidelity**:
   - Stay faithful to the source material's facts and arguments
   - If the source cites research or people, include those citations
   - Do NOT hallucinate facts, studies, or quotes not in the source
   - Each panelist should speak through their expertise lens

6. **Avoid**:
   - Jargon without explanation
   - Overly academic or stilted language
   - Repetitive phrasing or ideas
   - Artificial transitions ("That's a great point, let me add...")

7. **Segment Markers**: Use `### Segment N: Title` to mark major sections

## OUTPUT FORMAT

Begin with a title and brief intro, then the dialogue:

```
# [Entry Title]: A Panel Discussion

*A conversation exploring [topic] with [list panelist names and roles]*

---

**MODERATOR:** [Opening remarks]

### Segment 1: [Segment Title]

**PANELIST_1:** [Dialogue]

**PANELIST_2:** [Response]

[etc.]
```

Generate the complete script now."""

    return prompt


def generate_script(entry_data: dict, config: dict, model: str = "claude-sonnet-4-5"):
    """Generate podcast script using Claude with review and revision pass."""
    client = Anthropic()
    
    # Pass 1: Generate initial draft
    print(f"Generating initial draft for '{entry_data['title']}'...")
    print(f"Using model: {model}")
    
    initial_prompt = build_script_prompt(entry_data, config)
    
    initial_message = client.messages.create(
        model=model,
        max_tokens=16000,
        temperature=1.0,
        messages=[
            {"role": "user", "content": initial_prompt}
        ]
    )
    
    draft_script = initial_message.content[0].text
    initial_tokens = initial_message.usage.input_tokens + initial_message.usage.output_tokens
    
    print(f"✓ Initial draft generated ({initial_message.usage.output_tokens:,} tokens)")
    
    # Pass 2: Review and revise
    print(f"Reviewing and revising draft...")
    
    review_prompt = f"""You are reviewing a podcast script for accuracy and quality. Your task is to:

1. **Fact-check**: Verify all claims, examples, and research citations against the source material
2. **Improve flow**: Ensure the conversation feels natural and engaging
3. **Check characterization**: Verify each panelist stays in character and speaks from their expertise
4. **Enhance clarity**: Simplify jargon, improve explanations, ensure accessibility

SOURCE MATERIAL:
{entry_data['content']}

DRAFT SCRIPT TO REVIEW:
{draft_script}

Please provide a REVISED SCRIPT that:
- Corrects any factual errors or misrepresentations of the source material
- Removes or corrects any hallucinated facts, studies, or examples not in the source
- Improves dialogue flow and naturalness
- Ensures each panelist's voice is distinct and appropriate
- Maintains the same structure and format as the original

Output the complete revised script, not just corrections."""

    revision_message = client.messages.create(
        model=model,
        max_tokens=16000,
        temperature=0.7,  # Lower temperature for more careful revision
        messages=[
            {"role": "user", "content": review_prompt}
        ]
    )
    
    final_script = revision_message.content[0].text
    revision_tokens = revision_message.usage.input_tokens + revision_message.usage.output_tokens
    
    # Calculate total cost
    total_input_tokens = initial_message.usage.input_tokens + revision_message.usage.input_tokens
    total_output_tokens = initial_message.usage.output_tokens + revision_message.usage.output_tokens
    
    # Pricing for Claude Sonnet 4.5 (as of Jan 2026)
    input_cost = (total_input_tokens / 1_000_000) * 3.00
    output_cost = (total_output_tokens / 1_000_000) * 15.00
    total_cost = input_cost + output_cost
    
    print(f"✓ Script reviewed and revised ({revision_message.usage.output_tokens:,} tokens)")
    print(f"✓ Total: {total_output_tokens:,} tokens, ${total_cost:.3f}")
    
    return final_script, {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cost": total_cost,
        "passes": 2
    }



def save_script(script: str, collection: str, entry_slug: str):
    """Save generated script to file."""
    output_dir = Path(__file__).parent.parent / "outputs" / collection / "scripts"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / f"{entry_slug}.md"
    
    with open(output_path, "w") as f:
        f.write(script)
    
    print(f"✓ Script saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate podcast scripts from Alexandria Press entries")
    parser.add_argument("--collection", required=True, help="Collection name (e.g., practices)")
    parser.add_argument("--entry", help="Entry slug (e.g., fasting)")
    parser.add_argument("--all", action="store_true", help="Generate scripts for all entries")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Claude model to use")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    if args.collection not in config["collections"]:
        print(f"Error: Collection '{args.collection}' not configured")
        print(f"Available collections: {', '.join(config['collections'].keys())}")
        return 1
    
    # Determine which entries to process
    if args.all:
        # Load all entries from book.json
        book_path = Path(__file__).parent.parent / "outputs" / args.collection / "book.json"
        with open(book_path) as f:
            book_data = json.load(f)
        entry_slugs = [e["slug"] for e in book_data["entries"]]
    elif args.entry:
        entry_slugs = [args.entry]
    else:
        print("Error: Must specify either --entry or --all")
        return 1
    
    # Generate scripts
    total_cost = 0.0
    results = []
    
    for slug in entry_slugs:
        try:
            entry_data = load_entry(args.collection, slug)
            script, stats = generate_script(entry_data, config, args.model)
            output_path = save_script(script, args.collection, slug)
            
            total_cost += stats["cost"]
            results.append({
                "entry": slug,
                "success": True,
                "cost": stats["cost"],
                "output": str(output_path)
            })
            
            print()
            
        except Exception as e:
            print(f"✗ Error generating script for '{slug}': {e}")
            results.append({
                "entry": slug,
                "success": False,
                "error": str(e)
            })
            print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"Generated: {successful}/{len(results)} scripts")
    print(f"Total cost: ${total_cost:.2f}")
    
    if successful > 0:
        print(f"\nScripts saved to: outputs/{args.collection}/scripts/")
    
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
