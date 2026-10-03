import os
import re
import json
import base64
import requests
from typing import Optional, Dict, Any

class SarvamService:
    """
    Client for Sarvam AI Speech & Language APIs:
    - Speech-to-Text (STT): Saaras v3/v4 multilingual audio transcription & language detection
    - Translation: Indian language translation to/from English
    - Text-to-Speech (TTS): Bulbul v3 expressive Indian voice synthesis
    """
    BASE_URL = "https://api.sarvam.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SARVAM_AI_API_KEY", "sk_ooz2jl2s_96DIQueJ8rB014GS4d26IMxs")
        if not self.api_key:
            print("[SarvamService Warning] SARVAM_AI_API_KEY is not set.")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "api-subscription-key": self.api_key
        }

    def detect_script_language(self, text: str) -> str:
        """
        Fast, zero-latency language detector based on Unicode script block analysis.
        """
        counts = {
            "te-IN": len(re.findall(r"[\u0C00-\u0C7F]", text)), # Telugu
            "hi-IN": len(re.findall(r"[\u0900-\u097F]", text)), # Hindi / Marathi
            "ta-IN": len(re.findall(r"[\u0B80-\u0BFF]", text)), # Tamil
            "kn-IN": len(re.findall(r"[\u0C80-\u0CFF]", text)), # Kannada
            "ml-IN": len(re.findall(r"[\u0D00-\u0D7F]", text)), # Malayalam
            "bn-IN": len(re.findall(r"[\u0980-\u09FF]", text)), # Bengali
            "gu-IN": len(re.findall(r"[\u0A80-\u0AFF]", text)), # Gujarati
            "pa-IN": len(re.findall(r"[\u0A00-\u0A7F]", text)), # Punjabi
        }
        best_lang, max_count = max(counts.items(), key=lambda x: x[1])
        if max_count > 3:
            return best_lang
        return "en-IN"

    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav", model: str = "saaras:v3") -> Dict[str, Any]:
        """
        Transcribes speech audio using Sarvam Saaras model.
        Returns: { 'transcript': str, 'language_code': str, 'language_probability': float }
        """
        url = f"{self.BASE_URL}/speech-to-text"
        files = {
            "file": (filename, audio_bytes, "audio/wav")
        }
        data = {
            "model": model
        }
        try:
            res = requests.post(url, headers=self.headers, files=files, data=data, timeout=30)
            if res.status_code != 200:
                print(f"[Sarvam STT Error] {res.status_code}: {res.text}")
                return {"transcript": "", "language_code": "en-IN", "error": res.text}
            
            result = res.json()
            return {
                "transcript": result.get("transcript", ""),
                "language_code": result.get("language_code", "en-IN"),
                "language_probability": result.get("language_probability", 1.0)
            }
        except Exception as e:
            print(f"[Sarvam STT Exception] {e}")
            return {"transcript": "", "language_code": "en-IN", "error": str(e)}

    def translate(self, text: str, source_language_code: str = "auto", target_language_code: str = "en-IN") -> str:
        """
        Translates text between Indian languages and English using Sarvam Translate API.
        Chunks input if longer than 900 characters to stay within API limit.
        """
        if not text or not text.strip():
            return ""
        if source_language_code == target_language_code:
            return text

        url = f"{self.BASE_URL}/translate"
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }

        # Chunk text by paragraphs or sentences
        paragraphs = text.split("\n\n")
        translated_paragraphs = []

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            
            # Split if paragraph exceeds 850 characters
            sub_chunks = [p_clean[i:i+850] for i in range(0, len(p_clean), 850)]
            for chunk in sub_chunks:
                payload = {
                    "input": chunk,
                    "source_language_code": source_language_code,
                    "target_language_code": target_language_code,
                    "mode": "formal"
                }
                try:
                    res = requests.post(url, headers=headers, json=payload, timeout=20)
                    if res.status_code == 200:
                        data = res.json()
                        translated_paragraphs.append(data.get("translated_text", chunk))
                    else:
                        print(f"[Sarvam Translate Warning] {res.status_code}: {res.text}")
                        translated_paragraphs.append(chunk)
                except Exception as err:
                    print(f"[Sarvam Translate Exception] {err}")
                    translated_paragraphs.append(chunk)

        return "\n\n".join(translated_paragraphs)

    def text_to_speech(self, text: str, target_language_code: str = "en-IN", speaker: str = "kavya") -> Optional[str]:
        """
        Synthesizes speech audio using Sarvam Bulbul:v3 model.
        Returns: base64 encoded audio string (WAV)
        """
        if not text or not text.strip():
            return None

        # Clean markdown characters for pleasant vocalization
        speech_text = re.sub(r"[*#_`>\[\]]", "", text)
        speech_text = re.sub(r"https?://\S+", "", speech_text)
        speech_text = re.sub(r"\n+", ". ", speech_text).strip()

        # Sarvam Bulbul takes up to 500 characters per segment.
        # We select the initial diagnostic & advisory core (up to 450 chars) for instant, responsive audio.
        if len(speech_text) > 450:
            sentences = speech_text.split(". ")
            speech_text = ""
            for s in sentences:
                if len(speech_text) + len(s) + 2 <= 450:
                    speech_text += s + ". "
                else:
                    break
            speech_text = speech_text.strip() or text[:400]

        url = f"{self.BASE_URL}/text-to-speech"
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }

        # Validate target language code supported by bulbul:v3
        supported_langs = ["hi-IN", "te-IN", "ta-IN", "kn-IN", "mr-IN", "en-IN", "bn-IN", "gu-IN", "ml-IN", "pa-IN", "or-IN"]
        lang = target_language_code if target_language_code in supported_langs else "en-IN"

        payload = {
            "inputs": [speech_text],
            "target_language_code": lang,
            "speaker": speaker,
            "model": "bulbul:v3"
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                audios = data.get("audios", [])
                if audios:
                    return audios[0]
            else:
                print(f"[Sarvam TTS Warning] {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[Sarvam TTS Exception] {e}")

        return None
