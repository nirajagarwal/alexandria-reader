import os
import google.genai as genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

for model in client.models.list(config={"page_size": 100}):
    if "image" in model.name or "generate" in model.name or "flash" in model.name:
        print(model.name)
