import argparse
import json
import os
import glob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_dir = os.path.join(base_dir, "data", "raw", args.crop)
    
    if not os.path.exists(raw_dir):
        print(f"No raw data for {args.crop}")
        return
        
    files = glob.glob(os.path.join(raw_dir, "*.json"))
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        content = data.get("content", "")
        print(f"\n{args.crop.upper()} RAW DOCUMENT")
        print(f"Source: {data.get('organization')}")
        print(f"URL: {data.get('source_url')}")
        print(f"Title: {data.get('title')}")
        print(f"Characters: {len(content)}")
        print("Preview:")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 50)

if __name__ == "__main__":
    main()
