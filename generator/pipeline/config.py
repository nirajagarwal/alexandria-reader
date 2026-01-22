import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Models
ANTHROPIC_MODEL = "claude-sonnet-4-5"
IMAGEN_MODEL = "gemini-3-pro-image-preview"
EMBEDDING_MODEL = "text-embedding-004"

# Paths
# Assumes this file is in generator/pipeline/config.py
BASE_DIR = Path(__file__).parent.parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
ENTITIES_DIR = BASE_DIR / "entities"
OUTPUT_DIR = BASE_DIR / "outputs"

# Pipeline Defaults
DEFAULT_WORKERS = 5
MAX_RETRIES = 3
