# Podcast Script Generator - README

## Setup

1. **Install dependencies** (if not already done):
   ```bash
   source venv/bin/activate
   pip install python-dotenv
   ```

2. **Set your Anthropic API key**:
   
   Add to `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
   
   Or export as environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Generate a single script

```bash
source venv/bin/activate
python3 scripts/generate_podcast_script.py --collection practices --entry fasting
```

### Generate scripts for all entries in a collection

```bash
python3 scripts/generate_podcast_script.py --collection practices --all
```

### Use a different Claude model

```bash
python3 scripts/generate_podcast_script.py --collection practices --entry fasting --model claude-opus-4-20250514
```

## Output

Scripts are saved to: `outputs/{collection}/scripts/{entry_slug}.md`

For example: `outputs/practices/scripts/fasting.md`

## Cost

Using Claude Sonnet 4.5 with two-pass generation (draft + review):
- ~$1.00-2.00 per script (two passes)
- ~$30-50 for a full collection (27 entries)

The two-pass system ensures:
1. Initial creative draft
2. Fact-checking and revision against source material

## Configuration

Edit `scripts/podcast_config.json` to:
- Customize panelist personas
- Adjust target duration
- Modify conversation style guidelines
