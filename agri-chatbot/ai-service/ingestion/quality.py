import argparse
import json
import os
import glob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    manifest_path = os.path.join(base_dir, "data", "manifests", "manifest.json")
    
    docs_attempted = 0
    docs_success = 0
    docs_failed = 0
    
    stats_agg = {
        "segments_generated": 0,
        "llm_calls_successful": 0,
        "llm_calls_failed": 0,
        "object_responses": 0,
        "array_responses": 0,
        "objects_extracted": 0,
        "objects_recovered_from_arrays": 0,
        "objects_validated": 0,
        "objects_rejected": 0,
        "objects_deduplicated": 0
    }
    
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        for m in manifest:
            if m.get("crop") == args.crop:
                docs_attempted += 1
                if m.get("status") in ["processed", "partially_processed"]:
                    docs_success += 1
                elif m.get("status") in ["crawl_failed", "extraction_failed", "rejected"]:
                    docs_failed += 1
                
                s = m.get("stats", {})
                for k in stats_agg:
                    stats_agg[k] += s.get(k, 0)
                
    proc_file = os.path.join(base_dir, "data", "processed", args.crop, f"{args.crop}_knowledge.jsonl")
    objs = []
    if os.path.exists(proc_file):
        with open(proc_file, "r", encoding="utf-8") as f:
            for line in f:
                objs.append(json.loads(line))
                
    rej_file = os.path.join(base_dir, "data", "processed", "rejected", "rejected.jsonl")
    rej_count = 0
    if os.path.exists(rej_file):
        with open(rej_file, "r", encoding="utf-8") as f:
            for line in f:
                o = json.loads(line)
                if o.get("crop") == args.crop:
                    rej_count += 1
            
    print(f"\n{args.crop.upper()} DATA QUALITY REPORT")
    print("-" * 40)
    print(f"Documents attempted: {docs_attempted}")
    print(f"Documents crawled successfully: {docs_success}")
    print(f"Documents failed: {docs_failed}")
    print(f"\nSegments generated: {stats_agg['segments_generated']}")
    print(f"LLM calls successful: {stats_agg['llm_calls_successful']}")
    print(f"LLM calls failed: {stats_agg['llm_calls_failed']}")
    print(f"\nSingle-object responses: {stats_agg['object_responses']}")
    print(f"Array responses: {stats_agg['array_responses']}")
    print(f"Objects recovered from arrays: {stats_agg['objects_recovered_from_arrays']}")
    
    print(f"\nObjects extracted: {stats_agg['objects_extracted']}")
    print(f"Objects validated: {stats_agg['objects_validated']}")
    print(f"Objects rejected: {stats_agg['objects_rejected']}")
    print(f"Objects deduplicated/skipped: {stats_agg['objects_deduplicated']}")
    print(f"Current Knowledge Objects in JSONL: {len(objs)}")

    img_file = os.path.join(base_dir, "data", "processed", args.crop, f"{args.crop}_images.jsonl")
    img_count = 0
    if os.path.exists(img_file):
        with open(img_file, "r", encoding="utf-8") as f:
            for _ in f:
                img_count += 1
    print(f"Image URLs recorded in dataset: {img_count}")
    
    topics = {}
    for obj in objs:
        t = obj.get("topic", "unknown")
        topics[t] = topics.get(t, 0) + 1
        
    print("\nTopic-wise coverage:")
    for t, count in topics.items(): print(f"{t}: {count}")
    
    simulated = sum(1 for obj in objs if "simulated" in obj.get("content", "").lower())
    print(f"\nSimulated records: {simulated}")

if __name__ == "__main__":
    main()
