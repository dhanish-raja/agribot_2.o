import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

class InteractiveLLMExtractor:
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
            
        prompt = f"""
        Extract structured agricultural information regarding Diseases from the following text segment.
        The crop is: {meta['crop']}. The section is: {segment['section_title']}.

        
        CRITICAL RULES:
        - Extract ALL relevant agricultural facts, especially Symptoms, Development, and Control.
        - Create a SEPARATE knowledge object for each distinct subtopic (e.g., one for Symptoms, one for Development, one for Control).
        - DO NOT summarize everything into one generic object if multiple facts exist.
        - Use ONLY information present in the supplied source text.
        - Do not use general model knowledge.
        - Do not infer missing values.
        - Do not invent recommendations, doses, treatments, varieties, or schedules.
        - Use null when information is unavailable.
        - Return ONLY a valid JSON ARRAY of objects matching this schema exactly:
        
        [
          {{
            "crop": "string",
            "topic": "disease_management",
            "subtopic": "string (Symptoms, Development, Control, etc.)",
            "information_type": "string",
            "growth_stage": "string or null",
            "disease": "string (e.g. Anthracnose) or null",
            "scientific_name": "string or null",
            "pest": "string or null",
            "content": "string (the actual factual recommendation/description)"
          }}
        ]
        
        TEXT SEGMENT:
        {segment['content']}
        """
        
        try:
            response = self.model.generate_content(prompt)
            raw_json = response.text.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3].strip()
            
            data = json.loads(raw_json)
            
            results = []
            if isinstance(data, list):
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
                
            return results
        except Exception as e:
            raise Exception(f"LLM Extraction failed: {e}")
