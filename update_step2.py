import os
import shutil
import json

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/ai-service"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Clean previous simulated data
for d in ["data/raw", "data/processed", "data/manifests"]:
    d_path = os.path.join(base_dir, "..", d)
    if os.path.exists(d_path):
        shutil.rmtree(d_path)
    os.makedirs(d_path, exist_ok=True)

# 2. Comprehensive sources.json
sources = [
    # MANGO
    {"crop": "mango", "organization": "ICAR", "source_type": "web", "priority": "primary", "category": "cultivation", "url": "https://mango-crop.web.app/", "description": "Mango Crop Management System"},
    {"crop": "mango", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "cultivation", "url": "https://agritech.tnau.ac.in/horticulture/horti_fruits_mango.html", "description": "TNAU Mango"},
    # COCONUT
    {"crop": "coconut", "organization": "ICAR-CPCRI", "source_type": "web", "priority": "primary", "category": "practices", "url": "https://cpcri.gov.in/page/farmers_corner_package_practices", "description": "Package of Practices"},
    # SUGARCANE
    {"crop": "sugarcane", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "cultivation", "url": "https://agritech.tnau.ac.in/agriculture/sugarcrops_sugarcane.html", "description": "TNAU Sugarcane"},
    # TOBACCO
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "soils-climate", "url": "https://nirca.icar.gov.in/farmers.php?page=soils-climate", "description": "Soils and Climate"},
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "diseases", "url": "https://nirca.icar.gov.in/farmers.php?page=diseases", "description": "Disease Management"},
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "insects", "url": "https://nirca.icar.gov.in/farmers.php?page=insects", "description": "Insect Management"},
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "curing", "url": "https://nirca.icar.gov.in/farmers.php?page=curing", "description": "Curing"},
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "economy", "url": "https://nirca.icar.gov.in/farmers.php?page=economy", "description": "Economy"},
    # RICE
    {"crop": "rice", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "diseases", "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_cereals_rice_main.html", "description": "Rice Disease Database"},
    {"crop": "rice", "organization": "IRRI", "source_type": "web", "priority": "primary", "category": "diseases", "url": "https://rice-diseases.irri.org/contents", "description": "IRRI Rice Diseases"},
    {"crop": "rice", "organization": "ICAR-IIRR", "source_type": "web", "priority": "primary", "category": "databases", "url": "https://www.icar-iirr.org/index.php/en/services/databases", "description": "ICAR-IIRR Databases"},
    # CROSS-CROP
    {"crop": "all", "organization": "CABI", "source_type": "web", "priority": "secondary", "category": "knowledge_bank", "url": "https://plantwiseplusknowledgebank.org/", "description": "PlantwisePlus Knowledge Bank"},
    {"crop": "all", "organization": "GOI", "source_type": "web", "priority": "secondary", "category": "statistics", "url": "https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0", "description": "Crop Statistics"}
]
write_file("ingestion/sources/sources.json", json.dumps(sources, indent=2))

# 3. CrawlerService (Real Crawl4AI)
write_file("crawler/crawl_service.py", """
import asyncio
import datetime
import uuid
from crawl4ai import AsyncWebCrawler

class CrawlerService:
    async def crawl_url_async(self, url, source_meta):
        try:
            print(f"Crawling {url}...")
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                if not result or not result.markdown:
                    return None, "Empty content or failed to crawl."
                
                doc = {
                    "document_id": str(uuid.uuid4()),
                    "crop": source_meta["crop"],
                    "organization": source_meta["organization"],
                    "source": source_meta["organization"],
                    "source_url": url,
                    "title": result.metadata.get("title", f"Document from {url}") if hasattr(result, "metadata") and result.metadata else f"Document from {url}",
                    "retrieved_at": datetime.datetime.now().isoformat(),
                    "content": result.markdown
                }
                return doc, None
        except Exception as e:
            return None, str(e)
            
    def crawl_url(self, url, source_meta):
        return asyncio.run(self.crawl_url_async(url, source_meta))
""")

# 4. Content Cleaner (Removing navigation, HTML artifacts, duplicate paragraphs)
write_file("ingestion/cleaner.py", """
import re

class ContentCleaner:
    def clean(self, raw_doc):
        text = raw_doc.get("content", "")
        text = re.sub(r"\\n{3,}", "\\n\\n", text)
        lines = text.split("\\n")
        cleaned_lines = []
        seen_lines = set()
        
        for line in lines:
            line_stripped = line.strip()
            if len(line_stripped) < 3 and not any(c.isdigit() for c in line_stripped):
                continue
            if line_stripped in seen_lines and len(line_stripped) > 50:
                continue
            seen_lines.add(line_stripped)
            cleaned_lines.append(line)
            
        return "\\n".join(cleaned_lines)
""")

# 5. Segmenter (Heading aware)
write_file("ingestion/segmenter.py", """
import re

class DocumentSegmenter:
    def segment(self, clean_text):
        segments = []
        current_title = "General"
        current_content = []
        
        for line in clean_text.split("\\n"):
            if line.startswith("#"):
                if current_content:
                    segments.append({
                        "section_title": current_title,
                        "content": "\\n".join(current_content).strip()
                    })
                current_title = line.strip("# ").strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_content:
            segments.append({
                "section_title": current_title,
                "content": "\\n".join(current_content).strip()
            })
            
        return [s for s in segments if len(s["content"]) > 10]
""")

# 6. Real LLM Extractor (Google Generative AI)
write_file("ingestion/extractor.py", """
import os
import json
import google.generativeai as genai

class LLMExtractor:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def extract(self, segment, meta):
        if not self.model:
            raise Exception("LLM_API_KEY environment variable is not set. Cannot perform real extraction.")
            
        prompt = f\"\"\"
        Extract structured agricultural information from the following text segment.
        The crop is: {meta['crop']}. The section is: {segment['section_title']}.
        
        CRITICAL RULES:
        - Extract only information supported by the provided source.
        - Never use general knowledge to fill missing information.
        - Never invent dosage, fertilizer, pesticide, or disease management instructions.
        - Use null when information is unavailable.
        - Return ONLY a valid JSON object matching this schema:
        
        {{
          "crop": "string",
          "topic": "string (cultivation, soil, climate, disease, etc.)",
          "subtopic": "string",
          "information_type": "string",
          "growth_stage": "string",
          "disease": "string or null",
          "pest": "string or null",
          "content": "string (the actual factual recommendation/description)"
        }}
        
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
            data["source"] = meta["source"]
            data["organization"] = meta["organization"]
            data["source_url"] = meta["source_url"]
            data["document_name"] = meta["title"]
            data["page_number"] = None
            data["section"] = segment["section_title"]
            data["region"] = "India"
            data["language"] = "en"
            return data
        except Exception as e:
            raise Exception(f"LLM Extraction failed: {e}")
""")

# 7. Validator (reject simulated content)
write_file("ingestion/validator.py", """
class DataValidator:
    def validate(self, extracted_obj):
        if not extracted_obj.get("crop") in ["mango", "coconut", "sugarcane", "tobacco", "rice", "all"]:
            return False, "Invalid crop"
        if not extracted_obj.get("content"):
            return False, "Empty content"
        
        content = extracted_obj["content"].lower()
        if "simulated crawled content" in content or "dummy content" in content or "mock content" in content:
            return False, "Contains simulated content"
            
        if not extracted_obj.get("source_url"):
            return False, "Missing source URL"
            
        return True, ""
""")

# 8. Manifest (duplicate detection using SHA-256)
write_file("ingestion/manifest.py", """
import os
import json
import hashlib

class ManifestManager:
    def __init__(self, manifest_dir):
        self.manifest_path = os.path.join(manifest_dir, "manifest.json")
        os.makedirs(manifest_dir, exist_ok=True)
        if not os.path.exists(self.manifest_path):
            with open(self.manifest_path, "w") as f:
                json.dump([], f)
                
    def load(self):
        with open(self.manifest_path, "r") as f:
            return json.load(f)
            
    def save(self, data):
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=2)
            
    def get_hash(self, text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
        
    def is_processed(self, content_text):
        h = self.get_hash(content_text)
        data = self.load()
        return any(entry.get("content_hash") == h and entry.get("status") == "processed" for entry in data)
            
    def append(self, entry):
        data = self.load()
        data.append(entry)
        self.save(data)
""")

# 9. CLI Runner
write_file("ingestion/run.py", """
import argparse
import json
import os
import time
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
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    with open(os.path.join(os.path.dirname(__file__), "sources", "sources.json"), "r") as f:
        sources = json.load(f)

    if args.crop:
        sources = [s for s in sources if s["crop"] == args.crop]

    if args.dry_run:
        print("DRY RUN: The following sources would be processed:")
        for s in sources:
            print(f"- {s['url']}")
        return

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
            manifest.append({"source_url": src["url"], "status": "failed", "error": str(error)})
            continue
            
        if manifest.is_processed(raw_doc["content"]):
            print(f"SKIPPED {src['url']}: Already processed (duplicate content hash).")
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
        
        success_count = 0
        for seg in segments:
            try:
                extracted = extractor.extract(seg, raw_doc)
                is_valid, reason = validator.validate(extracted)
                if is_valid:
                    with open(os.path.join(proc_dir, f"{src['crop']}_knowledge.jsonl"), "a", encoding="utf-8") as f:
                        f.write(json.dumps(extracted, ensure_ascii=False) + "\\n")
                    success_count += 1
                else:
                    extracted["reject_reason"] = reason
                    with open(os.path.join(rej_dir, "rejected.jsonl"), "a", encoding="utf-8") as f:
                        f.write(json.dumps(extracted, ensure_ascii=False) + "\\n")
            except Exception as e:
                print(f"Extraction error on segment '{seg['section_title'][:30]}': {e}")
                
        content_hash = manifest.get_hash(raw_doc["content"])
        manifest.append({
            "document_id": raw_doc["document_id"],
            "source_url": src["url"],
            "status": "processed",
            "content_hash": content_hash,
            "segments_processed": success_count,
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

if __name__ == "__main__":
    main()
""")

# 10. Inspect Raw
write_file("ingestion/inspect_raw.py", """
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
        print(f"\\n{args.crop.upper()} RAW DOCUMENT")
        print(f"Source: {data.get('organization')}")
        print(f"URL: {data.get('source_url')}")
        print(f"Title: {data.get('title')}")
        print(f"Characters: {len(content)}")
        print("Preview:")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 50)

if __name__ == "__main__":
    main()
""")

# 11. Quality Report
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
    attempted = 0
    downloaded = 0
    failed = 0
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        for m in manifest:
            attempted += 1
            if m.get("status") == "processed":
                downloaded += 1
            elif m.get("status") == "failed":
                failed += 1
                
    raw_dir = os.path.join(base_dir, "data", "raw", args.crop)
    raw_docs = len(glob.glob(os.path.join(raw_dir, "*.json"))) if os.path.exists(raw_dir) else 0
    
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
            rej_count = sum(1 for _ in f)
            
    print(f"\\n{args.crop.upper()} DATA QUALITY REPORT")
    print(f"Documents attempted: {attempted}")
    print(f"Successfully downloaded: {downloaded}")
    print(f"Failed: {failed}")
    print(f"Raw documents (this crop): {raw_docs}")
    print(f"Extracted knowledge objects: {len(objs)}")
    print(f"Rejected: {rej_count}")
    
    sources = set(obj.get("source") for obj in objs)
    print("\\nSources:")
    for s in sources: print(f"- {s}")
    
    topics = {}
    for obj in objs:
        t = obj.get("topic", "unknown")
        topics[t] = topics.get(t, 0) + 1
        
    print("\\nTopics:")
    for t, count in topics.items(): print(f"{t}: {count}")
    
    simulated = sum(1 for obj in objs if "simulated" in obj.get("content", "").lower())
    print(f"\\nSimulated records: {simulated}")

if __name__ == "__main__":
    main()
""")

print("Successfully generated all files.")
