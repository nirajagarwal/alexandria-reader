import os
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

model = "gemini-2.5-flash-image"
prompt = "A simple red circle"

print(f"Testing {model}...")

# Test 1: generate_images
try:
    print("Attempting generate_images...")
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1)
    )
    print("✓ generate_images success")
except Exception as e:
    print(f"✗ generate_images failed: {e}")

# Test 2: generate_content
try:
    print("\nAttempting generate_content...")
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    print("✓ generate_content success")
    print(response)
except Exception as e:
    print(f"✗ generate_content failed: {e}")
