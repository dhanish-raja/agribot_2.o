import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiEmbedder:
    """
    Generates text embeddings using Google Gemini models/gemini-embedding-001 (768-dim)
    with automatic multi-key rotation on 429 quota exhaustion.
    """
    def __init__(self, env_path=None, output_dimensionality=768, model_name="models/gemini-embedding-001"):
        if env_path and os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()
            
        keys_str = os.getenv("LLM_API_KEYS", "")
        if keys_str:
            self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        else:
            single = os.getenv("LLM_API_KEY", "")
            self.api_keys = [single.strip()] if single.strip() else []
            
        self.current_key_idx = 0
        self.model_name = model_name
        self.output_dimensionality = output_dimensionality
        self._configure_active_key()

    def _configure_active_key(self):
        if self.api_keys and self.current_key_idx < len(self.api_keys):
            active_key = self.api_keys[self.current_key_idx]
            genai.configure(api_key=active_key)
            print(f"[GeminiEmbedder] Active Key [{self.current_key_idx + 1}/{len(self.api_keys)}] ({active_key[:12]}...) | Model: {self.model_name}")
        else:
            raise Exception("No active Gemini API keys available for embeddings.")

    def rotate_key(self):
        self.current_key_idx += 1
        if self.current_key_idx < len(self.api_keys):
            print(f"[GeminiEmbedder] Quota reached. Rotating to Key [{self.current_key_idx + 1}/{len(self.api_keys)}]...")
            self._configure_active_key()
            return True
        else:
            print(f"[GeminiEmbedder] ALERT: All {len(self.api_keys)} API keys exhausted!")
            return False

    def embed_texts(self, texts, task_type="retrieval_document"):
        """
        Embed a list of text strings in batches with automatic key rotation and rate limiting.
        """
        if not texts:
            return []
            
        while True:
            try:
                res = genai.embed_content(
                    model=self.model_name,
                    content=texts,
                    task_type=task_type,
                    output_dimensionality=self.output_dimensionality
                )
                raw_embed = res.get("embedding", [])
                if isinstance(texts, str):
                    return [raw_embed]
                return raw_embed
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "resourceexhausted" in err_str:
                    if self.rotate_key():
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(f"All {len(self.api_keys)} Gemini keys exhausted quota: {e}")
                else:
                    raise e
