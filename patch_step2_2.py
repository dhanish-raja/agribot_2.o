import os
import json

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/ai-service"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

write_file("ingestion/extractor.py", """
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

class LLMExtractor:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LLM_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def extract(self, segment, meta):
        if not self.model:
            raise Exception("LLM_API_KEY environment variable is not set. Cannot perform real extraction.")
            
        prompt = f\"\"\"
        Extract structured agricultural information from the following text segment.
        The crop is: {meta['crop']}. The section is: {segment['section_title']}.
        
        CRITICAL RULES:
        - Extract ALL relevant agricultural facts.
        - Create a SEPARATE knowledge object for each distinct topic (e.g. soil, irrigation, fertilizer, variety).
        - DO NOT summarize everything into one generic object if multiple facts exist.
        - Use ONLY information present in the supplied source text.
        - Do not use general model knowledge.
        - Do not infer missing values.
        - Do not invent recommendations, doses, treatments, varieties, or schedules.
        - Use null when information is unavailable.
        - Return ONLY a valid JSON ARRAY of objects matching this schema:
        
        [
          {{
            "crop": "string",
            "topic": "string (cultivation, soil, climate, disease, etc.)",
            "subtopic": "string",
            "information_type": "string",
            "growth_stage": "string or null",
            "disease": "string or null",
            "pest": "string or null",
            "content": "string (the actual factual recommendation/description)"
          }}
        ]
        
        TEXT SEGMENT:
        {segment['content']}
        \"\"\"
        
        try:
            response = self.model.generate_content(prompt)
            raw_json = response.text.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3].strip()
            
            data = json.loads(raw_json)
            
            results = []
            response_type = "object"
            if isinstance(data, list):
                response_type = "array"
                items = data
            else:
                items = [data]
                
            for item in items:
                if not isinstance(item, dict):
                    continue
                item["source"] = meta["source"]
                item["organization"] = meta["organization"]
                item["source_url"] = meta["source_url"]
                item["document_name"] = meta["title"]
                item["page_number"] = None
                item["section"] = segment["section_title"]
                item["region"] = "India"
                item["language"] = "en"
                results.append(item)
                
            return {
                "response_type": response_type,
                "objects": results
            }
        except Exception as e:
            raise Exception(f"LLM Extraction failed: {e}")
""")

write_file("ingestion/run.py", """
import argparse
import json
import os
import time
import hashlib
from crawler.crawl_service import CrawlerService
from ingestion.cleaner import ContentCleaner
from ingestion.segmenter import DocumentSegmenter
from ingestion.extractor import LLMExtractor
from ingestion.validator import DataValidator
from ingestion.manifest import ManifestManager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    with open(os.path.join(os.path.dirname(__file__), "sources", "sources.json"), "r") as f:
        sources = json.load(f)

    if args.crop:
        sources = [s for s in sources if s["crop"] == args.crop]

    crawler = CrawlerService()
    cleaner = ContentCleaner()
    segmenter = DocumentSegmenter()
    extractor = LLMExtractor()
    validator = DataValidator()
    manifest = ManifestManager(os.path.join(base_dir, "data", "manifests"))

    for src in sources:
        print(f"Processing source: {src['url']}")
        raw_doc, error = crawler.crawl_url(src["url"], src)
        
        if error or not raw_doc:
            print(f"FAILED to crawl {src['url']}: {error}")
            manifest.append({
                "crop": src["crop"],
                "source_url": src["url"], 
                "status": "crawl_failed", 
                "error": str(error)
            })
            continue
            
        raw_dir = os.path.join(base_dir, "data", "raw", src["crop"])
        os.makedirs(raw_dir, exist_ok=True)
        with open(os.path.join(raw_dir, f"{raw_doc['document_id']}.json"), "w", encoding="utf-8") as f:
            json.dump(raw_doc, f, ensure_ascii=False)
            
        clean_text = cleaner.clean(raw_doc)
        segments = segmenter.segment(clean_text)
        
        proc_dir = os.path.join(base_dir, "data", "processed", src["crop"])
        os.makedirs(proc_dir, exist_ok=True)
        rej_dir = os.path.join(base_dir, "data", "processed", "rejected")
        os.makedirs(rej_dir, exist_ok=True)
        
        stats = {
            "segments_generated": len(segments),
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
        
        seen_hashes = set()
        
        jsonl_path = os.path.join(proc_dir, f"{src['crop']}_knowledge.jsonl")
        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        content_str = str(obj.get("content", "")) + str(obj.get("topic", ""))
                        seen_hashes.add(hashlib.sha256(content_str.encode("utf-8")).hexdigest())
                    except:
                        pass
        
        for seg in segments:
            try:
                result = extractor.extract(seg, raw_doc)
                stats["llm_calls_successful"] += 1
                
                resp_type = result["response_type"]
                objects = result["objects"]
                
                if resp_type == "object":
                    stats["object_responses"] += 1
                else:
                    stats["array_responses"] += 1
                    
                stats["objects_extracted"] += len(objects)
                if resp_type == "array":
                    stats["objects_recovered_from_arrays"] += len(objects)
                
                for obj in objects:
                    is_valid, reason = validator.validate(obj)
                    if is_valid:
                        content_str = str(obj.get("content", "")) + str(obj.get("topic", ""))
                        obj_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
                        
                        if obj_hash in seen_hashes:
                            stats["objects_deduplicated"] += 1
                            continue
                            
                        seen_hashes.add(obj_hash)
                        stats["objects_validated"] += 1
                        with open(jsonl_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(obj, ensure_ascii=False) + "\\n")
                    else:
                        stats["objects_rejected"] += 1
                        obj["reject_reason"] = reason
                        with open(os.path.join(rej_dir, "rejected.jsonl"), "a", encoding="utf-8") as f:
                            f.write(json.dumps(obj, ensure_ascii=False) + "\\n")
            except Exception as e:
                stats["llm_calls_failed"] += 1
                print(f"Extraction error on segment '{seg['section_title'][:30]}': {e}")
                
        # Determine status
        status = "processed"
        if stats["llm_calls_failed"] > 0 and stats["objects_validated"] > 0:
            status = "partially_processed"
        elif stats["llm_calls_failed"] > 0 and stats["objects_validated"] == 0:
            status = "extraction_failed"
        elif stats["segments_generated"] > 0 and stats["objects_validated"] == 0 and stats["objects_rejected"] == 0:
            status = "extraction_failed"
            
        content_hash = manifest.get_hash(raw_doc["content"])
        manifest.append({
            "crop": src["crop"],
            "document_id": raw_doc["document_id"],
            "source_url": src["url"],
            "status": status,
            "content_hash": content_hash,
            "stats": stats,
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

if __name__ == "__main__":
    main()
""")

write_file("ingestion/quality.py", """
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
            
    print(f"\\n{args.crop.upper()} DATA QUALITY REPORT")
    print("-" * 40)
    print(f"Documents attempted: {docs_attempted}")
    print(f"Documents crawled successfully: {docs_success}")
    print(f"Documents failed: {docs_failed}")
    print(f"\\nSegments generated: {stats_agg['segments_generated']}")
    print(f"LLM calls successful: {stats_agg['llm_calls_successful']}")
    print(f"LLM calls failed: {stats_agg['llm_calls_failed']}")
    print(f"\\nSingle-object responses: {stats_agg['object_responses']}")
    print(f"Array responses: {stats_agg['array_responses']}")
    print(f"Objects recovered from arrays: {stats_agg['objects_recovered_from_arrays']}")
    
    print(f"\\nObjects extracted: {stats_agg['objects_extracted']}")
    print(f"Objects validated: {stats_agg['objects_validated']}")
    print(f"Objects rejected: {stats_agg['objects_rejected']}")
    print(f"Objects deduplicated/skipped: {stats_agg['objects_deduplicated']}")
    
    topics = {}
    for obj in objs:
        t = obj.get("topic", "unknown")
        topics[t] = topics.get(t, 0) + 1
        
    print("\\nTopic-wise coverage:")
    for t, count in topics.items(): print(f"{t}: {count}")
    
    simulated = sum(1 for obj in objs if "simulated" in obj.get("content", "").lower())
    print(f"\\nSimulated records: {simulated}")

if __name__ == "__main__":
    main()
""")

print("Successfully patched Step 2.2 files.")
