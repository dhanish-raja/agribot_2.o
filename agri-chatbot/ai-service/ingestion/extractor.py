import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

class LLMExtractor:
    def __init__(self):
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()
        keys_str = os.getenv("LLM_API_KEYS", "")
        if keys_str:
            self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        else:
            single_key = os.getenv("LLM_API_KEY", "")
            self.api_keys = [single_key.strip()] if single_key.strip() else []

        self.current_key_idx = 0
        self.model_name = os.getenv("LLM_MODEL", "gemini-flash-latest")
        # Ensure compatible model
        if self.model_name == "gemini-2.5-flash":
            self.model_name = "gemini-flash-latest"

        self._configure_current_key()

    def _configure_current_key(self):
        if self.api_keys and self.current_key_idx < len(self.api_keys):
            active_key = self.api_keys[self.current_key_idx]
            genai.configure(api_key=active_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"[LLMExtractor] Active Gemini Key: [{self.current_key_idx + 1}/{len(self.api_keys)}] ({active_key[:12]}...) | Model: {self.model_name}")
        else:
            self.model = None

    def rotate_key(self):
        self.current_key_idx += 1
        if self.current_key_idx < len(self.api_keys):
            print(f"[LLMExtractor] Quota limit encountered. Automatically rotating to Key [{self.current_key_idx + 1}/{len(self.api_keys)}]...")
            self._configure_current_key()
            return True
        else:
            print(f"[LLMExtractor] ALERT: ALL {len(self.api_keys)} API keys have been exhausted!")
            return False

    def extract(self, segment, meta):
        if not self.model:
            raise Exception("No active LLM API keys configured. Cannot perform real extraction.")

        prompt = f"""
        Extract structured agricultural information from the following text segment.
        The crop is: {meta.get('crop', 'mango')}. The section is: {segment.get('section_title', 'General')}.
        
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
        """

        # Retry loop across available keys
        while True:
            try:
                response = self.model.generate_content(prompt)
                raw_json = response.text.strip()
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:-3].strip()
                elif raw_json.startswith("```"):
                    raw_json = raw_json[3:-3].strip()

                try:
                    data = json.loads(raw_json, strict=False)
                except Exception:
                    # Try finding the first JSON array or object in the response
                    import re
                    match = re.search(r'\[.*\]', raw_json, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0), strict=False)
                    else:
                        match_obj = re.search(r'\{.*\}', raw_json, re.DOTALL)
                        if match_obj:
                            data = json.loads(match_obj.group(0), strict=False)
                        else:
                            raise

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
                    item["source"] = meta.get("source", "Unknown")
                    item["organization"] = meta.get("organization", "Unknown")
                    item["source_url"] = meta.get("source_url", "")
                    item["document_name"] = meta.get("title", "")
                    item["page_number"] = None
                    item["section"] = segment.get("section_title", "General")
                    item["region"] = "India"
                    item["language"] = "en"
                    results.append(item)

                return {
                    "response_type": response_type,
                    "objects": results
                }

            except Exception as e:
                err_str = str(e).lower()
                # Check for 429 quota error or resource exhausted
                if "429" in err_str or "quota" in err_str or "resourceexhausted" in err_str:
                    rotated = self.rotate_key()
                    if rotated:
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(f"All {len(self.api_keys)} Gemini API keys have exhausted their quota: {e}")
                elif "404" in err_str and "model" in err_str:
                    # Model fallback
                    print(f"[LLMExtractor] Model {self.model_name} not found. Switching to gemini-flash-latest...")
                    self.model_name = "gemini-flash-latest"
                    self._configure_current_key()
                    continue
                else:
                    raise Exception(f"LLM Extraction failed: {e}")
