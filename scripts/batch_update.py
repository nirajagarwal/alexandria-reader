#!/usr/bin/env python3
"""
Batch Update Script for Alexandria Press
Runs the generator pipeline for ALL collections found in the entities directory.
Useful for backfilling EPUBs, DOCX, and DB updates.
"""

import sys
import subprocess
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent
ENTITIES_DIR = BASE_DIR / "entities"
PIPELINE_SCRIPT = BASE_DIR / "generator" / "run_pipeline.py"

def main():
    print("="*60)
    print("Alexandria Press - Batch Update")
    print("="*60)

    # Find all collections
    json_files = sorted(list(ENTITIES_DIR.glob("*.json")))
    collections = [f.stem for f in json_files]
    
    print(f"Found {len(collections)} collections: {', '.join(collections)}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, collection_id in enumerate(collections, 1):
        print(f"[{i}/{len(collections)}] Processing: {collection_id}")
        print("-" * 40)
        
        try:
            # Run pipeline with skip-existing to avoid regeneration
            cmd = [
                sys.executable, 
                str(PIPELINE_SCRIPT), 
                "--collection", collection_id,
                "--skip-existing"
            ]
            
            # Run and capture output to avoid visual clutter, print if error
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Success: {collection_id}")
                success_count += 1
            else:
                print(f"✗ Failed: {collection_id}")
                print(f"Error Output:\n{result.stderr}")
                fail_count += 1
                
        except Exception as e:
            print(f"✗ Exception: {e}")
            fail_count += 1
            
        print("\n")

    print("="*60)
    print(f"Batch Update Complete")
    print(f"Success: {success_count}")
    print(f"Failed:  {fail_count}")
    print("="*60)

if __name__ == "__main__":
    main()
