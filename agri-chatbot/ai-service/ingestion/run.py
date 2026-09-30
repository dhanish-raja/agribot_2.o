import argparse
import sys
import json
import os
import time
import hashlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from crawler.crawl_service import CrawlerService
from ingestion.cleaner import ContentCleaner
from ingestion.segmenter import DocumentSegmenter
from ingestion.extractor import LLMExtractor
from ingestion.validator import DataValidator
from ingestion.manifest import ManifestManager

def get_urls_for_crop(crop, base_dir):
    urls = []
    sources_file = os.path.join(base_dir, "data", "sources", f"{crop}.txt")
    if os.path.exists(sources_file):
        with open(sources_file, "r") as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith("#"):
                    urls.append(url)
    return urls

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str)
    parser.add_argument("--url", type=str)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--backup", action="store_true", help="Create snapshot backup before running")
    parser.add_argument("--rebuild", action="store_true", help="Full rebuild (requires --confirm-rebuild)")
    parser.add_argument("--confirm-rebuild", action="store_true", help="Safety confirmation for full rebuild")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agri-chatbot", "ai-service"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    data_dir = os.path.join(base_dir, "data")
    if args.backup:
        from ingestion.backup import create_backup
        b_path, b_items = create_backup(data_dir)
        print(f"Pre-ingestion backup created at: {b_path} ({b_items})")

    if args.rebuild:
        if not args.confirm_rebuild:
            print("ERROR: --rebuild specified without --confirm-rebuild. Aborting to protect existing data!")
            sys.exit(1)
        else:
            print("WARNING: Confirmed rebuild requested. Creating automatic backup before rebuild...")
            from ingestion.backup import create_backup
            create_backup(data_dir)
            # Rebuild logic if explicitly requested


    crops_to_run = []
    if args.all:
        crops_to_run = ["mango", "coconut", "sugarcane", "tobacco", "rice"]
    elif args.crop:
        crops_to_run = [args.crop]
        
    crawler = CrawlerService()
    cleaner = ContentCleaner()
    segmenter = DocumentSegmenter()
    extractor = LLMExtractor()
    validator = DataValidator()
    manifest = ManifestManager(os.path.join(base_dir, "data", "manifests"))

    for crop in crops_to_run:
        urls = []
        if args.url:
            urls.append(args.url)
        else:
            urls = get_urls_for_crop(crop, base_dir)
            
        already_processed_urls = set()
        mf_path = os.path.join(base_dir, "data", "manifests", "manifest.json")
        if os.path.exists(mf_path):
            try:
                with open(mf_path, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    for entry in mdata:
                        if entry.get("crop") == crop and entry.get("status") == "processed":
                            already_processed_urls.add(entry.get("source_url"))
            except:
                pass

        for idx, url in enumerate(urls):
            if url in already_processed_urls:
                print(f"[{idx+1}/{len(urls)}] Skipping already processed source: {url}")
                continue

            print(f"\n[{idx+1}/{len(urls)}] Processing source: {url}")
            source_meta = {
                "crop": crop,
                "organization": "ICAR/Gov" if "icar" in url or "gov" in url else "TNAU" if "tnau" in url else "Unknown",
                "source_url": url
            }
            
            raw_doc, error = crawler.crawl_url(url, source_meta)
            
            if error or not raw_doc:
                print(f"FAILED to crawl {url}: {error}")
                manifest.append({
                    "crop": crop,
                    "source_url": url, 
                    "status": "crawl_failed", 
                    "error": str(error)
                })
                continue
                
            raw_dir = os.path.join(base_dir, "data", "raw", crop)
            os.makedirs(raw_dir, exist_ok=True)
            with open(os.path.join(raw_dir, f"{raw_doc['document_id']}.json"), "w", encoding="utf-8") as f:
                json.dump(raw_doc, f, ensure_ascii=False)
                
            clean_text = cleaner.clean(raw_doc)
            segments = segmenter.segment(clean_text)
            
            proc_dir = os.path.join(base_dir, "data", "processed", crop)
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
                "objects_deduplicated": 0,
                "interactive_crawl_used": raw_doc.get("interactive_crawl_used", False),
                "image_urls_found": 0
            }
            
            jsonl_path = os.path.join(proc_dir, f"{crop}_knowledge.jsonl")
            images_path = os.path.join(proc_dir, f"{crop}_images.jsonl")
            
            seen_image_urls = set()
            if os.path.exists(images_path):
                with open(images_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            iobj = json.loads(line)
                            if "image_url" in iobj:
                                seen_image_urls.add(iobj["image_url"])
                        except:
                            pass

            if "extracted_images" in raw_doc:
                stats["image_urls_found"] = len(raw_doc["extracted_images"])
                with open(images_path, "a", encoding="utf-8") as f:
                    for img in raw_doc["extracted_images"]:
                        if img.get("image_url") not in seen_image_urls:
                            seen_image_urls.add(img.get("image_url"))
                            f.write(json.dumps(img, ensure_ascii=False) + "\n")
            
            seen_hashes = set()
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
                        stats["objects_recovered_from_arrays"] += len(objects)
                        
                    stats["objects_extracted"] += len(objects)
                    
                    with open(jsonl_path, "a", encoding="utf-8") as f:
                        for obj in objects:
                            content_str = str(obj.get("content", "")) + str(obj.get("topic", ""))
                            obj_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
                            
                            if obj_hash in seen_hashes:
                                stats["objects_deduplicated"] += 1
                                continue
                                
                            is_valid, reason = validator.validate(obj)
                            if is_valid:
                                stats["objects_validated"] += 1
                                seen_hashes.add(obj_hash)
                                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                            else:
                                stats["objects_rejected"] += 1
                                with open(os.path.join(rej_dir, "rejected.jsonl"), "a", encoding="utf-8") as rf:
                                    rf.write(json.dumps({"object": obj, "reason": reason}, ensure_ascii=False) + "\n")
                except Exception as e:
                    stats["llm_calls_failed"] += 1
                    print(f"Extraction error on segment '{seg['section_title'][:30]}': {e}")
                    
            status = "processed"
            if stats["llm_calls_failed"] > 0 and stats["objects_validated"] > 0:
                status = "partially_processed"
            elif stats["llm_calls_failed"] > 0 and stats["objects_validated"] == 0 and stats["objects_deduplicated"] == 0:
                status = "extraction_failed"
            elif stats["segments_generated"] > 0 and stats["objects_validated"] == 0 and stats["objects_rejected"] == 0:
                if stats["objects_deduplicated"] > 0:
                    status = "processed"
                else:
                    status = "extraction_failed"
                
            content_hash = manifest.get_hash(raw_doc["content"])
            manifest.append({
                "crop": crop,
                "document_id": raw_doc["document_id"],
                "source_url": url,
                "status": status,
                "content_hash": content_hash,
                "stats": stats,
                "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

if __name__ == "__main__":
    main()
