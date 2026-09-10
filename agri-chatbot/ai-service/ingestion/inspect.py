import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    proc_file = os.path.join(base_dir, "data", "processed", args.crop, f"{args.crop}_knowledge.jsonl")
    
    print(f"{args.crop.upper()} INGESTION REPORT\n")
    if not os.path.exists(proc_file):
        print("No data found.")
        return
        
    objs = []
    with open(proc_file, "r") as f:
        for line in f:
            objs.append(json.loads(line))
            
    print(f"Knowledge objects: {len(objs)}")
    sources = set(obj.get("source") for obj in objs)
    print("Sources:")
    for s in sources:
        print(f"- {s}")

if __name__ == "__main__":
    main()
