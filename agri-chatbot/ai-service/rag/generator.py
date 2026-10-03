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

class GeminiGenerator:
    """
    RAG LLM generator powered by Google Gemini with instant multi-key failover rotation.
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
            
        # Default starting index is 7 which is verified active with gemini-2.5-flash
        self.current_key_idx = 7 if len(self.api_keys) > 7 else 0
        self.model_name = model_name

    def _configure_key(self, key_idx: int):
        if not self.api_keys or key_idx >= len(self.api_keys):
            raise RuntimeError("No active Gemini API keys remaining in key pool.")
        key = self.api_keys[key_idx]
        genai.configure(api_key=key)

    RELEVANCE_THRESHOLD = 0.65  # Strict threshold matching Slide 6 Reliability Controls

    def generate_rag_answer(self, query: str, context_chunks: list, crop: str = None) -> dict:
        """
        Given the farmer query and retrieved vector context chunks, generate a grounded answer.
        Applies strict relevance threshold cutoff matching Slide 6 reliability controls.
        """
        top_score = context_chunks[0].get("score", 0.0) if context_chunks else 0.0

        if not context_chunks or top_score < self.RELEVANCE_THRESHOLD:
            crop_label = f" for {crop.capitalize()}" if crop else ""
            return {
                "answer": (
                    f"I could not find sufficiently reliable information in trusted agricultural sources{crop_label} to answer this question. "
                    "To prevent crop damage from unverified advice, please consult your local Krishi Vigyan Kendra (KVK) officer or an agricultural extension specialist."
                ),
                "crop": crop,
                "confidence": "Low",
                "sources": [
                    {
                        "crop": hit.get("payload", {}).get("crop", "General"),
                        "topic": hit.get("payload", {}).get("topic", "General"),
                        "source": hit.get("payload", {}).get("source_file", "Knowledge Base"),
                        "similarity_score": round(float(hit.get("score", 0.0)), 4)
                    } for hit in (context_chunks[:2] if context_chunks else [])
                ],
                "suggested_questions": [
                    "What are the 5 major crops supported by AgriBot?",
                    "How to manage major diseases in Rice?",
                    "What is the fertilizer schedule for Coconut?"
                ]
            }

        # Build context prompt
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

        # Calculate confidence from top score
        top_score = context_chunks[0].get("score", 0.0)
        confidence = "High" if top_score >= 0.75 else ("Medium" if top_score >= 0.60 else "Low")

        # Call Gemini with instant failover
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
                # Successful call, record this working key
                self.current_key_idx = key_idx
                raw_text = response.text.strip()
                
                # Extract follow up questions if present
                answer_text = raw_text
                follow_ups = []
                if "FOLLOW_UP_QUESTIONS:" in raw_text:
                    parts = raw_text.split("FOLLOW_UP_QUESTIONS:")
                    answer_text = parts[0].strip()
                    q_lines = parts[1].strip().split("\n")
                    for q in q_lines:
                        q_clean = re.sub(r"^[-*\d.\s]+", "", q).strip()
                        if q_clean:
                            follow_ups.append(q_clean)
                            
                return {
                    "answer": answer_text,
                    "crop": crop or (context_chunks[0].get("payload", {}).get("crop")),
                    "confidence": confidence,
                    "sources": sources[:3],
                    "suggested_questions": follow_ups[:3]
                }
            except Exception as e:
                # Instant key rotation without 39s sleep
                attempts += 1

        # Fallback if all keys fail
        return {
            "answer": f"All AI generation keys are currently at maximum rate limits. Here is the direct verified excerpt from our knowledge base:\n\n{context_chunks[0].get('payload', {}).get('text', '')[:600]}...",
            "crop": crop,
            "confidence": confidence,
            "sources": sources[:3],
            "suggested_questions": []
        }
