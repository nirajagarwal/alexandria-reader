import os
import io
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configuration
INPUT_DIR = Path("images/originals")
OUTPUT_DIR = Path("images/output")
MODEL_NAME = "gemini-3-pro-image-preview" # or 2.0-flash-exp if 3 not avail? User said 3.
PROMPT = "Create a pencil sketch using this image."
TARGET_WIDTH = 600

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)

def process_image(client, image_path):
    print(f"Processing {image_path.name}...")
    
    try:
        # Open source image
        with Image.open(image_path) as img:
            # Prepare contents
            # google-genai client handles PIL images directly in contents
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[PROMPT, img]
            )
            
            # Extract image from response
            image_data = None
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        break
            elif hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        break
            
            if not image_data:
                print(f"  No image found in response for {image_path.name}")
                return

            # Process output image
            with Image.open(io.BytesIO(image_data)) as out_img:
                # Resize
                aspect_ratio = out_img.height / out_img.width
                new_height = int(TARGET_WIDTH * aspect_ratio)
                resized_img = out_img.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)
                
                # Save
                output_path = OUTPUT_DIR / f"{image_path.stem}.png"
                resized_img.save(output_path, "PNG")
                print(f"  Saved to {output_path}")

    except Exception as e:
        print(f"  Error processing {image_path.name}: {e}")

def main():
    if not INPUT_DIR.exists():
        print(f"Input directory not found: {INPUT_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    client = get_client()
    
    # Process images
    # Supports common image extensions
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
    
    for file_path in INPUT_DIR.iterdir():
        if file_path.suffix.lower() in extensions:
            process_image(client, file_path)
            
    print("Done.")

if __name__ == "__main__":
    main()
