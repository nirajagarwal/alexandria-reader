# Alexandria Press

> **Books only AI can write.**

Alexandria Press publishes AI-generated book collections that explore vast subjects with consistent depth and care. These are not cheap knockoffs of human writing, but a new genre of reference materials where the machine's ability to remain tireless across hundreds of entries is its greatest strength.

## The Mission

Earn respect through substance. The AI-generated nature of the work is stated plainly, not cached as a novelty. We aim for a reading experience where the design disappears and only the content remains.

## Project Structure

```text
alexandria-press/
├── api/             # FastAPI backend serving JSON content
├── db/              # Database schema and loading scripts (Turso/SQLite)
├── frontend/        # Vanilla HTML/CSS/JS viewer
├── generator/       # Python scripts for book & cover generation
├── prompts/         # System prompts for different collections
├── entities/        # Source metadata for collections (e.g., periodic-tales.json)
└── outputs/         # Generated markdown entries and book assets
```

## Getting Started

### 1. Requirements

- Python 3.10+
- Anthropic API Key (for text generation)
- Google Gemini API Key (for cover generation)
- Turso Database (URL + Auth Token)

### 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd alexandria-press

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment

Create a `.env` file in the root:

```env
ANTHROPIC_API_KEY=your_key
GEMINI_API_KEY=your_key
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your_token
```

## Usage

### Generation

To generate a new collection (e.g., Periodic Tales):

```bash
python generator/generate.py --collection periodic-tales --workers 10
```

This will generate individual markdown entries in `outputs/periodic-tales/entries/` and assemble them into a `book.json`.

### Database Loading

Initialize the schema and load the book into Turso:

```bash
python db/load_db.py --book outputs/periodic-tales/book.json --init-schema
```

### Running the Development Server

The easiest way to start developing is to use the `dev.sh` script. This handles environment variables and starts the API with hot-reload enabled:

```bash
./dev.sh
```

Once running, the library is available at [http://localhost:8000](http://localhost:8000).

### Manual Setup
If you prefer to run components separately:

#### 1. Running the API
Start the FastAPI server with manual reload:
```bash
uvicorn api.main:app --reload
```

#### 2. Viewing the Library
You can serve the `frontend/` directory with any static server (or access it through the API as shown above):
```bash
npx serve frontend
```

## The Aesthetic

- **Invisible Design:** Restraint that conveys reverence.
- **Typography:** Serif (`Cormorant Garamond`) for content, clean sans (`IBM Plex Sans`) for UI.
- **Color:** Parchment light mode and Vault dark mode. Monochromatic with warmth.
- **Interaction:** Subtle transitions, keyboard navigation support.

---

Published by [alexandria.press](https://alexandria.press)
