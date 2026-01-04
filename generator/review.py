"""
Alexandria Press - Editorial Review & Revision

Post-processing step that sends generated content back for evaluation
and revision. Returns revised content in the same format.

Usage:
    from review import review_and_revise
    
    revised_content = review_and_revise(
        content=generated_markdown,
        collection_id="body",
        entity_name="Breathing"
    )
"""

import os
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-5"

# =============================================================================
# Review Prompt
# =============================================================================

REVIEW_PROMPT = """You are an editor for alexandria.press, reviewing AI-generated entries before publication.

## Your Task

Review the entry below. Check for:

1. **Repetition across vignettes** — Has any concept, term, or fact been restated? Each vignette should cover distinct territory. If surfactant is explained in one vignette, it should not be explained again in another.

2. **Weak opening** — Does the main biography begin with mechanics or description before earning interest? The opening should pull the reader in, not describe.

3. **Circling** — Does the entry keep returning to the same ideas in different words?

4. **Voice violations:**
   - Rhetorical questions
   - Metacommentary ("interestingly," "remarkably," "it's worth noting")
   - Exclamation points
   - Emdashes (should use periods, commas, or restructure)
   - "You" or "your" (should be third person with room for universal statements)
   - Forced wonder or sentiment
   - Medical jargon without explanation

5. **Vignette title quality** — Are titles concrete and specific, or generic labels like "Mechanism" or "Cultural Aspects"?

6. **Flow** — Does the prose flow naturally with varied sentence length, or is it choppy/monotonous?

7. **Completeness** — Are the key relationships covered: physical event, sensation, mechanism, evolutionary context, lifecycle, failure modes, cultural weight?

## Your Output

If the entry passes review with no significant issues, respond with exactly:

APPROVED

If the entry needs revision, respond with the complete revised entry in the same markdown format. Do not explain your changes. Do not add commentary. Just output the revised entry, complete and ready to publish.

## Collection Context

Collection: {collection_id}
Entry: {entity_name}

## Entry to Review

{content}
"""

# =============================================================================
# Review Function
# =============================================================================

def get_client():
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def review_and_revise(
    content: str,
    collection_id: str,
    entity_name: str,
    max_revisions: int = 2
) -> str:
    """
    Send content for editorial review and revision.
    
    Args:
        content: The generated markdown content
        collection_id: The collection ID (e.g., "body", "periodic-tales")
        entity_name: The entity name (e.g., "Breathing", "Hydrogen")
        max_revisions: Maximum revision passes (default 2)
    
    Returns:
        The approved or revised content
    """
    client = get_client()
    current_content = content
    
    for revision_num in range(max_revisions):
        prompt = REVIEW_PROMPT.format(
            collection_id=collection_id,
            entity_name=entity_name,
            content=current_content
        )
        
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response = message.content[0].text.strip()
        
        if response == "APPROVED":
            return current_content
        
        # Response is the revised content
        current_content = response
    
    # Return after max revisions even if not explicitly approved
    return current_content


def review_entry_file(filepath: str, collection_id: str) -> str:
    """
    Review an entry from a file.
    
    Args:
        filepath: Path to the markdown file
        collection_id: The collection ID
    
    Returns:
        The approved or revised content
    """
    with open(filepath, "r") as f:
        content = f.read()
    
    # Extract entity name from first line (# Entity Name)
    first_line = content.split("\n")[0]
    entity_name = first_line.lstrip("# ").strip()
    
    return review_and_revise(content, collection_id, entity_name)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Review and revise generated entries")
    parser.add_argument("--file", required=True, help="Path to markdown file")
    parser.add_argument("--collection", required=True, help="Collection ID")
    parser.add_argument("--output", help="Output path (default: overwrite input)")
    parser.add_argument("--max-revisions", type=int, default=2, help="Max revision passes")
    
    args = parser.parse_args()
    
    with open(args.file, "r") as f:
        content = f.read()
    
    first_line = content.split("\n")[0]
    entity_name = first_line.lstrip("# ").strip()
    
    print(f"Reviewing: {entity_name}")
    
    revised = review_and_revise(
        content=content,
        collection_id=args.collection,
        entity_name=entity_name,
        max_revisions=args.max_revisions
    )
    
    output_path = args.output or args.file
    with open(output_path, "w") as f:
        f.write(revised)
    
    if revised == content:
        print("Approved without changes.")
    else:
        print(f"Revised. Saved to: {output_path}")