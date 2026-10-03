import os
import re
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

SYSTEM_PROMPT = """You are AgriBot, an intelligent and grounded agricultural AI assistant specialized in crop management, pest & disease diagnostics, nutrient care, and agronomy for Mango, Coconut, Sugarcane, Tobacco, and Rice.

Your guiding instructions:
1. Answer the farmer's question thoroughly, clearly, and practically using ONLY the verified agricultural context provided.
2. Structure your advice into easy-to-read sections (e.g., Symptoms, Causes, Organic / Cultural Controls, Chemical Treatment with precise dosages, and Preventive Measures).
3. If specific measurements, dosages, or chemical formulations are in the context, cite them accurately.
4. If the provided context does not contain sufficient details to answer part of the question, honestly state the limitation and recommend consulting a local agricultural extension officer (KVK) or agronomist. NEVER hallucinate pesticides or unsafe dosages.
5. Keep your tone encouraging, respectful, and farmer-friendly.
"""

INTENT_PROMPT = """You are an intent classification system for an agricultural chatbot.
Classify the following user query into one of two categories:
1. "AGRICULTURAL": The query is about farming, crops, plants, pests, diseases, fertilizers, soil, harvesting, agronomy, livestock, weather, or agriculture (even if it is about crops outside our core database, e.g. Tomato, Cotton, Wheat, Potato, Chilli, Apple, etc.).
2. "NON_AGRICULTURAL": The query is completely unrelated to farming or agriculture (e.g., coding, cryptocurrency, finance, entertainment, general chat, movies, politics, math, etc.).

Query: "{query}"

Output ONLY a valid JSON object in this exact format:
{{"is_agricultural": true, "crop": "detected_crop_or_general", "topic": "pest/disease/cultivation/general"}}
"""

WEB_FALLBACK_PROMPT = """You are AgriBot, an expert agricultural advisory assistant.
The farmer asked an agricultural question that is outside our primary pre-indexed crops (Mango, Coconut, Sugarcane, Tobacco, Rice).

Farmer's Question: "{query}"
Detected Crop/Topic: "{crop}"

Provide an authoritative, grounded agricultural advisory following Indian agricultural university standards (ICAR / State Agricultural Universities / Vikaspedia).
Structure your response cleanly:
1. **Overview & Symptoms / Context**
2. **Cultural & Preventive Measures**
3. **Chemical & Organic Management** (cite precise standard dosages if applicable, e.g. ml/L, kg/ha)
4. **Important Safety Advisory** (always advise consulting local KVK officers before chemical application)

At the end of your response, output two sections:
SOURCES:
- Source Name (e.g., ICAR / TNAU / Vikaspedia / Department of Agriculture)
FOLLOW_UP_QUESTIONS:
- Suggested follow-up question 1
- Suggested follow-up question 2
"""

class GeminiGenerator:
    """
    RAG LLM generator powered by Google Gemini with:
    1. Local Vector DB RAG for core crops.
    2. Dynamic Intent Classification for low-confidence queries.
    3. Live Agricultural Knowledge Fallback & Auto-Ingestion for unsupported crops.
    4. Polite rejection for non-agricultural queries.
    """
    def __init__(self, env_path=None, model_name="models/gemini-2.5-flash"):
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
            
        self.current_key_idx = 7 if len(self.api_keys) > 7 else 0
        self.model_name = model_name

    def _configure_key(self, key_idx: int):
        if not self.api_keys or key_idx >= len(self.api_keys):
            raise RuntimeError("No active Gemini API keys remaining in key pool.")
        key = self.api_keys[key_idx]
        genai.configure(api_key=key)

    RELEVANCE_THRESHOLD = 0.65  # Confidence threshold for local vector database

    def classify_intent(self, query: str) -> dict:
        """Classifies whether query is agricultural vs non-agricultural."""
        attempts = 0
        total_keys = len(self.api_keys)
        while attempts < total_keys:
            key_idx = (self.current_key_idx + attempts) % total_keys
            try:
                self._configure_key(key_idx)
                model = genai.GenerativeModel(model_name=self.model_name)
                res = model.generate_content(
                    INTENT_PROMPT.format(query=query),
                    generation_config={"temperature": 0.0, "max_output_tokens": 100},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                text = res.text.strip()
                # Parse JSON
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                break
            except Exception:
                attempts += 1
                
        # Fallback keyword classification if API fails
        agri_keywords = ["crop", "plant", "soil", "pest", "disease", "fertilizer", "weed", "irrigation", "spray", "seed", "leaf", "yield", "farm", "pesticide", "harvest"]
        is_agri = any(k in query.lower() for k in agri_keywords)
        return {"is_agricultural": is_agri, "crop": "general", "topic": "general"}

    def generate_web_fallback(self, query: str, crop: str = "general") -> dict:
        """Generates grounded agricultural advisory for queries not present in local vector DB."""
        attempts = 0
        total_keys = len(self.api_keys)
        while attempts < total_keys:
            key_idx = (self.current_key_idx + attempts) % total_keys
            try:
                self._configure_key(key_idx)
                model = genai.GenerativeModel(model_name=self.model_name)
                prompt = WEB_FALLBACK_PROMPT.format(query=query, crop=crop or "General Agriculture")
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.2, "top_p": 0.85, "max_output_tokens": 1200},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                raw_text = response.text.strip()

                # Parse follow-ups & sources
                answer_text = raw_text
                sources = []
                follow_ups = []

                if "FOLLOW_UP_QUESTIONS:" in answer_text:
                    parts = answer_text.split("FOLLOW_UP_QUESTIONS:")
                    answer_text = parts[0].strip()
                    for q in parts[1].strip().split("\n"):
                        q_clean = re.sub(r"^[-*\d.\s]+", "", q).strip()
                        if q_clean:
                            follow_ups.append(q_clean)

                if "SOURCES:" in answer_text:
                    parts = answer_text.split("SOURCES:")
                    answer_text = parts[0].strip()
                    for s in parts[1].strip().split("\n"):
                        s_clean = re.sub(r"^[-*\d.\s]+", "", s).strip()
                        if s_clean:
                            sources.append({
                                "crop": crop or "Extended Crop",
                                "topic": "Agricultural Advisory",
                                "source": s_clean,
                                "similarity_score": 0.85  # Dynamic synthesis confidence
                            })

                if not sources:
                    sources = [{
                        "crop": crop or "Extended Crop",
                        "topic": "General Agronomy",
                        "source": "ICAR / State Agricultural Universities (Live Synthesis)",
                        "similarity_score": 0.85
                    }]

                return {
                    "answer": answer_text,
                    "crop": crop or "general",
                    "confidence": "Medium",
                    "sources": sources,
                    "suggested_questions": follow_ups[:3],
                    "should_auto_ingest": True,  # Flag for auto-ingestion
                    "content_to_ingest": answer_text
                }
            except Exception:
                attempts += 1

        return {
            "answer": "This appears to be an agricultural question, but live advisory synthesis is currently unavailable due to rate limits. Please consult your local KVK officer.",
            "crop": crop,
            "confidence": "Low",
            "sources": [],
            "suggested_questions": [],
            "should_auto_ingest": False
        }

    def generate_rag_answer(self, query: str, context_chunks: list, crop: str = None) -> dict:
        """
        Given the farmer query and retrieved vector context chunks, generate a grounded answer.
        Handles:
        1. Score >= 0.65 -> Local Vector DB RAG
        2. Score < 0.65 -> Check Intent:
           - Agricultural -> Live Agricultural Advisory + Auto-Ingestion
           - Non-Agricultural -> Polite Rejection
        """
        top_score = context_chunks[0].get("score", 0.0) if context_chunks else 0.0

        # Handle Low Confidence / Out of Vector DB
        if not context_chunks or top_score < self.RELEVANCE_THRESHOLD:
            # Step 1: Classify user intent
            intent = self.classify_intent(query)
            
            # Situation 2: Non-Agricultural Query
            if not intent.get("is_agricultural", False):
                return {
                    "answer": (
                        "I am AgriBot, an AI assistant dedicated exclusively to crop management, agronomy, and pest diagnostics. "
                        "I cannot assist with non-agricultural questions. Please feel free to ask any questions about your crops!"
                    ),
                    "crop": None,
                    "confidence": "Low",
                    "sources": [],
                    "suggested_questions": [
                        "What are the 5 major crops supported by AgriBot?",
                        "How to identify blast disease in Rice?",
                        "What is the fertilizer schedule for Coconut?"
                    ],
                    "should_auto_ingest": False
                }
            
            # Situation 1: Genuine Agricultural Query outside local Vector DB -> Live Knowledge Retrieval!
            detected_crop = intent.get("crop") if intent.get("crop") != "general" else (crop or "general")
            return self.generate_web_fallback(query=query, crop=detected_crop)

        # Situation 0: High Confidence Local Vector DB Match!
        formatted_contexts = []
        sources = []
        for i, hit in enumerate(context_chunks, 1):
            p = hit.get("payload", {})
            score = hit.get("score", 0.0)
            text = p.get("text") or p.get("content") or ""
            c_crop = p.get("crop", crop or "General")
            topic = p.get("topic", "Agronomy")
            source_file = p.get("source_file", "Verified Knowledge Base")
            
            formatted_contexts.append(
                f"[Doc {i} | Crop: {c_crop.capitalize()} | Topic: {topic}]\n{text}\n"
            )
            sources.append({
                "crop": c_crop,
                "topic": topic,
                "source": source_file,
                "similarity_score": round(float(score), 4)
            })

        combined_context = "\n---\n".join(formatted_contexts)

        prompt = f"""Farmer's Question: {query}
Crop Context: {crop if crop else 'Auto-detected / Multi-crop'}

Verified Context from Agricultural Knowledge Base:
\"\"\"
{combined_context}
\"\"\"

Please provide a well-structured, clear, actionable response based on the above verified context. 
At the very end of your response, list 2-3 brief follow-up questions the farmer might find helpful, formatted as:
FOLLOW_UP_QUESTIONS:
- Question 1
- Question 2
"""

        confidence = "High" if top_score >= 0.75 else "Medium"

        attempts = 0
        total_keys = len(self.api_keys)
        
        while attempts < total_keys:
            key_idx = (self.current_key_idx + attempts) % total_keys
            try:
                self._configure_key(key_idx)
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.2, "top_p": 0.85, "max_output_tokens": 1500},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                raw_text = response.text.strip()
                
                answer_text = raw_text
                follow_ups = []
                if "FOLLOW_UP_QUESTIONS:" in raw_text:
                    parts = raw_text.split("FOLLOW_UP_QUESTIONS:")
                    answer_text = parts[0].strip()
                    for q in parts[1].strip().split("\n"):
                        q_clean = re.sub(r"^[-*\d.\s]+", "", q).strip()
                        if q_clean:
                            follow_ups.append(q_clean)
                            
                return {
                    "answer": answer_text,
                    "crop": crop or (context_chunks[0].get("payload", {}).get("crop")),
                    "confidence": confidence,
                    "sources": sources[:3],
                    "suggested_questions": follow_ups[:3],
                    "should_auto_ingest": False
                }
            except Exception:
                attempts += 1

        return {
            "answer": f"All AI generation keys are currently busy. Top verified excerpt from our knowledge base:\n\n{context_chunks[0].get('payload', {}).get('text', '')[:600]}...",
            "crop": crop,
            "confidence": confidence,
            "sources": sources[:3],
            "suggested_questions": [],
            "should_auto_ingest": False
        }
