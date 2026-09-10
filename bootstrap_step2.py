import os
import json

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/ai-service"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Sources JSON
sources = [
    {"crop": "mango", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "cultivation", "url": "https://agritech.tnau.ac.in/horticulture/horti_fruits_mango.html", "description": "TNAU Mango Cultivation"},
    {"crop": "mango", "organization": "ICAR", "source_type": "web", "priority": "primary", "category": "general", "url": "https://mango-crop.web.app/", "description": "Mango Crop Management System"},
    {"crop": "coconut", "organization": "ICAR-CPCRI", "source_type": "web", "priority": "primary", "category": "practices", "url": "https://cpcri.gov.in/page/farmers_corner_package_practices", "description": "Package of Practices"},
    {"crop": "sugarcane", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "cultivation", "url": "https://agritech.tnau.ac.in/agriculture/sugarcrops_sugarcane.html", "description": "TNAU Sugarcane"},
    {"crop": "tobacco", "organization": "ICAR-NIRCA", "source_type": "web", "priority": "primary", "category": "practices", "url": "https://nirca.icar.gov.in/farmers.php", "description": "NIRCA Farmers Section"},
    {"crop": "rice", "organization": "TNAU", "source_type": "web", "priority": "primary", "category": "diseases", "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_cereals_rice_main.html", "description": "Rice Disease Database"}
]
write_file("ingestion/sources/sources.json", json.dumps(sources, indent=2))

# 2. Crawler Service
write_file("crawler/crawl_service.py", """
import datetime
import uuid

class CrawlerService:
    def crawl_url(self, url, source_meta):
        print(f"Crawling {url}...")
        return {
            "document_id": str(uuid.uuid4()),
            "crop": source_meta["crop"],
            "organization": source_meta["organization"],
            "source": source_meta["organization"],
            "source_url": url,
            "title": f"Document from {url}",
            "retrieved_at": datetime.datetime.now().isoformat(),
            "content": f"Simulated crawled content for {source_meta[\"crop\"]} from {url}. Contains cultivation practices, diseases, and management."
        }
""")

# 3. Content Cleaner
write_file("ingestion/cleaner.py", """
class ContentCleaner:
    def clean(self, raw_data):
        return raw_data["content"].strip()
""")

# 4. Segmenter
write_file("ingestion/segmenter.py", """
class DocumentSegmenter:
    def segment(self, clean_text):
        return [{"section_title": "General", "content": clean_text}]
""")

# 5. LLM Extractor
write_file("ingestion/extractor.py", """
class LLMExtractor:
    def extract(self, segment, meta):
        return {
            "crop": meta["crop"],
            "topic": "cultivation",
            "subtopic": "general",
            "information_type": "general",
            "growth_stage": "all",
            "disease": None,
            "pest": None,
            "source": meta["source"],
            "organization": meta["organization"],
            "source_url": meta["source_url"],
            "document_name": meta["title"],
            "page_number": None,
            "section": segment["section_title"],
            "region": "India",
            "language": "en",
            "content": segment["content"]
        }
""")

# 6. Validator
write_file("ingestion/validator.py", """
class DataValidator:
    def validate(self, extracted_obj):
        if not extracted_obj["crop"] in ["mango", "coconut", "sugarcane", "tobacco", "rice"]:
            return False, "Invalid crop"
        if not extracted_obj["content"]:
            return False, "Empty content"
        return True, ""
""")

# 7. Manifest
write_file("ingestion/manifest.py", """
import os
import json

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
            
    def append(self, entry):
        data = self.load()
        data.append(entry)
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=2)
""")

# 8. CLI Runner
write_file("ingestion/run.py", """
import argparse
import json
import os
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
            print(f"- {s[\"url\"]}")
        return

    crawler = CrawlerService()
    cleaner = ContentCleaner()
    segmenter = DocumentSegmenter()
    extractor = LLMExtractor()
    validator = DataValidator()
    manifest = ManifestManager(os.path.join(base_dir, "data", "manifests"))

    for src in sources:
        print(f"Processing source: {src[\"url\"]}")
        raw_doc = crawler.crawl_url(src["url"], src)
        
        raw_dir = os.path.join(base_dir, "data", "raw", src["crop"])
        os.makedirs(raw_dir, exist_ok=True)
        with open(os.path.join(raw_dir, f"{raw_doc[\"document_id\"]}.json"), "w") as f:
            json.dump(raw_doc, f)
            
        clean_text = cleaner.clean(raw_doc)
        segments = segmenter.segment(clean_text)
        
        proc_dir = os.path.join(base_dir, "data", "processed", src["crop"])
        os.makedirs(proc_dir, exist_ok=True)
        rej_dir = os.path.join(base_dir, "data", "processed", "rejected")
        os.makedirs(rej_dir, exist_ok=True)
        
        for seg in segments:
            extracted = extractor.extract(seg, raw_doc)
            is_valid, reason = validator.validate(extracted)
            if is_valid:
                with open(os.path.join(proc_dir, f"{src[\"crop\"]}_knowledge.jsonl"), "a") as f:
                    f.write(json.dumps(extracted) + "\\n")
                manifest.append({"document_id": raw_doc["document_id"], "status": "processed"})
            else:
                extracted["reject_reason"] = reason
                with open(os.path.join(rej_dir, "rejected.jsonl"), "a") as f:
                    f.write(json.dumps(extracted) + "\\n")
                manifest.append({"document_id": raw_doc["document_id"], "status": "rejected"})

if __name__ == "__main__":
    main()
""")

# 9. Inspection Tool
write_file("ingestion/inspect.py", """
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True)
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    proc_file = os.path.join(base_dir, "data", "processed", args.crop, f"{args.crop}_knowledge.jsonl")
    
    print(f"{args.crop.upper()} INGESTION REPORT\\n")
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
""")

