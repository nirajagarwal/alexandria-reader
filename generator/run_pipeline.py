#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from generator.pipeline.pipeline import Pipeline

def main():
    parser = argparse.ArgumentParser(description="Alexandria Press - Book Generator Pipeline")
    parser.add_argument("--collection", required=True, help="Collection ID (e.g., periodic-tales)")
    parser.add_argument("--resume-from", type=int, default=0, help="Resume from entry index")
    parser.add_argument("--skip-existing", action="store_true", help="Skip entries that already have content")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    try:
        pipeline = Pipeline(
            collection_id=args.collection,
            resume_from=args.resume_from,
            skip_existing=args.skip_existing,
            workers=args.workers
        )
        pipeline.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
