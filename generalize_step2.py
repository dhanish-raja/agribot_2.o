import os
import json

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/ai-service"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Create source configuration files
sources_dir = os.path.join(base_dir, "..", "data", "sources")
os.makedirs(sources_dir, exist_ok=True)

mango_sources = """
https://mango-crop.web.app/
https://mango-crop.web.app/diseasemanage/dismgtanthra.htm
https://agritech.tnau.ac.in/horticulture/horti_fruits_mango.html
"""
with open(os.path.join(sources_dir, "mango.txt"), "w") as f:
    f.write(mango_sources.strip())
    
with open(os.path.join(sources_dir, "coconut.txt"), "w") as f:
    f.write("https://cpcri.gov.in/page/farmers_corner_package_practices")
    
with open(os.path.join(sources_dir, "sugarcane.txt"), "w") as f:
    f.write("https://agritech.tnau.ac.in/agriculture/sugarcrops_sugarcane.html")
    
with open(os.path.join(sources_dir, "tobacco.txt"), "w") as f:
    f.write("https://nirca.icar.gov.in/farmers.php?page=soils-climate")

with open(os.path.join(sources_dir, "rice.txt"), "w") as f:
    f.write("https://rice-diseases.irri.org/contents")

# 2. Adapters System
write_file("ingestion/adapters/__init__.py", "")
write_file("ingestion/adapters/base.py", """
class BaseAdapter:
    def can_handle(self, url):
        return False
    
    def process(self, url, raw_doc):
        # Return segments and images
        return [], []
""")

# 3. Crawler Service (Generic & Interactive)
write_file("crawler/crawl_service.py", """
import asyncio
import datetime
import uuid
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

class CrawlerService:
    def __init__(self):
        # Generic JS to unhide tabs, accordions, and modals
        self.generic_interactive_js = \"\"\"
        document.querySelectorAll('*').forEach(el => {
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') {
                el.style.display = 'block';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
            }
        });
        document.querySelectorAll('button, a, [role="button"], [role="tab"]').forEach(el => {
            let text = (el.innerText || '').toLowerCase();
            if(text.includes('symptom') || text.includes('control') || text.includes('read more') || text.includes('show more') || text.includes('detail')) {
                try { el.click(); } catch(e){}
            }
        });
        \"\"\"

    async def crawl_url_async(self, url, source_meta):
        try:
            print(f"Crawling {url}...")
            
            # 1. First attempt generic crawl without heavy JS
            config_static = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config_static)
                
                if not result or not result.markdown:
                    return None, "Empty content or failed to crawl."
                    
                # 2. Interactive Content Detection
                html = result.html or ""
                needs_interaction = False
                interactive_indicators = ['aria-expanded', 'aria-controls', 'display: none', 'display:none', 'modal', 'tab-content', 'accordion', 'hidden', 'symptoms and control!']
                
                for ind in interactive_indicators:
                    if ind.lower() in html.lower():
                        needs_interaction = True
                        break
                        
                if needs_interaction:
                    print(f"Interactive elements detected on {url}. Re-crawling with Playwright JS injection...")
                    config_interactive = CrawlerRunConfig(
                        js_code=[self.generic_interactive_js],
                        wait_for="js:() => true",
                        delay_before_return_html=2.0,
                        cache_mode=CacheMode.BYPASS
                    )
                    result = await crawler.arun(url=url, config=config_interactive)
                
                images = []
                if hasattr(result, 'media') and result.media and 'images' in result.media:
                    for img in result.media['images']:
                        if img.get('src'):
                            # Basic image categorization based on URL and Alt text
                            img_type = "general"
                            alt_text = str(img.get('alt', '')).lower()
                            if "symptom" in alt_text or "disease" in alt_text or "anthra" in url.lower():
                                img_type = "disease_symptom"
                                
                            images.append({
                                "crop": source_meta.get("crop", "unknown"),
                                "disease": "unknown" if img_type == "general" else "extracted from context",
                                "image_url": img.get('src'),
                                "source_url": url,
                                "image_type": img_type,
                                "source": source_meta.get("organization", "unknown"),
                                "organization": source_meta.get("organization", "unknown"),
                                "alt_text": img.get('alt', ''),
                                "score": img.get('score', 0)
                            })
                
                doc = {
                    "document_id": str(uuid.uuid4()),
                    "crop": source_meta.get("crop", "unknown"),
                    "organization": source_meta.get("organization", "unknown"),
                    "source": source_meta.get("organization", "unknown"),
                    "source_url": url,
                    "title": result.metadata.get("title", f"Document from {url}") if hasattr(result, "metadata") and result.metadata else f"Document from {url}",
                    "retrieved_at": datetime.datetime.now().isoformat(),
                    "content": result.markdown,
                    "html": result.html,
                    "extracted_images": images,
                    "interactive_crawl_used": needs_interaction
                }
                return doc, None
        except Exception as e:
            return None, str(e)
            
    def crawl_url(self, url, source_meta):
        return asyncio.run(self.crawl_url_async(url, source_meta))
""")

# 4. Extractor
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
        - Create a SEPARATE knowledge object for each distinct topic (e.g. soil, irrigation, fertilizer, variety, symptoms, development, control).
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
            "scientific_name": "string or null",
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

# 5. Run Script (Generic Pipeline)
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

def get_urls_for_crop(crop, base_dir):
    urls = []
    sources_file = os.path.join(base_dir, "..", "data", "sources", f"{crop}.txt")
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
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agri-chatbot", "ai-service"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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
            
        for url in urls:
            print(f"\\nProcessing source: {url}")
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
            
            if "extracted_images" in raw_doc:
                stats["image_urls_found"] = len(raw_doc["extracted_images"])
                with open(images_path, "a", encoding="utf-8") as f:
                    for img in raw_doc["extracted_images"]:
                        f.write(json.dumps(img, ensure_ascii=False) + "\\n")
            
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
                    
            status = "processed"
            if stats["llm_calls_failed"] > 0 and stats["objects_validated"] > 0:
                status = "partially_processed"
            elif stats["llm_calls_failed"] > 0 and stats["objects_validated"] == 0:
                status = "extraction_failed"
            elif stats["segments_generated"] > 0 and stats["objects_validated"] == 0 and stats["objects_rejected"] == 0:
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
""")

print("Successfully written generalized ingestion pipeline files.")
