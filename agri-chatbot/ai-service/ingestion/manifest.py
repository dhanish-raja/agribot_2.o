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
