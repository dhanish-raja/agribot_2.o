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
