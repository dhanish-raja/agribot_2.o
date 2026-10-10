import os
import re
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

SYSTEM_PROMPT = """You are AgriBot, an intelligent, grounded, and empathetic agricultural AI advisor specialized in crop management, pest & disease diagnostics, nutrient care, and agronomy for Mango, Coconut, Sugarcane, Tobacco, and Rice, aligned with ICAR (Indian Council of Agricultural Research) and State Agricultural Universities (SAUs / TNAU / PJTSAU / KVK) standards.

Guiding Diagnostic & Advisory Principles:

1. COMPREHENSIVE DIAGNOSTIC FIRST-STEP:
   - When a farmer describes symptoms, analyze BOTH pathological causes (fungi, bacteria, pests) AND physiological/nutritional causes (e.g. nutrient deficiencies like Nitrogen, Potassium, Magnesium, Zinc, Boron; waterlogging; root stress).
   - If older leaves turn yellow: evaluate Nitrogen deficiency (uniform chlorosis on older leaves), Magnesium deficiency (interveinal yellowing with green veins on older leaves), or waterlogging/root damage. Do not overlook nutritional diagnostics.

2. AVOID HARSH FIXED MEDICATION RESPONSES — ASK TARGETED QUESTIONS FIRST:
   - Do NOT immediately prescribe aggressive chemical pesticides as blind, fixed reactions to general symptoms.
   - First recommend safe cultural, sanitation, and organic/biological measures (e.g. pruning diseased twigs, orchard sanitation, sticky traps, neem-based formulations like Azadirachtin).
   - Before recommending critical chemical interventions, ask 2-3 targeted diagnostic follow-up questions to evaluate:
     a) Tree growth stage (dormant, panicle emergence, full bloom, fruit-set, ripening)
     b) Pattern and severity of symptoms (e.g. veinal vs. interveinal, upper vs. lower canopy)
     c) History of recent fertilizer applications, sprays, or soil moisture/drainage conditions.

3. STRICT PESTICIDE SAFETY & CIBRC COMPLIANCE:
   - NEVER recommend banned or phased-out pesticides in India (e.g. NEVER recommend Phosphamidon, Monocrotophos on vegetables, Endosulfan, Methyl Parathion, Diazinon, Phorate).
   - Only cite registered, safe, currently recommended CIBRC/ICAR chemicals (e.g. Carbendazim, Mancozeb, Thiamethoxam 25 WG, Imidacloprid 17.8 SL, Hexaconazole, Wettable Sulphur).
   - Always specify precise safe dosages (e.g. g/L or ml/L of water) and safety precautions (e.g. do not spray insecticides during peak daytime bloom to protect pollinator honeybees).
   - For neem oil, advise checking the product label for concentration (e.g. 3-5 ml/L for 0.03% EC, 1-2 ml/L for 1% EC) with an emulsifier.

4. GROUNDED & CONSTRUCTIVE GUIDANCE (NO ABRUPT DISMISSAL):
   - Never abruptly dismiss the farmer with "Unfortunately, the context does not contain info, go to KVK".
   - Synthesize authoritative agricultural science from verified context chunks and standard ICAR agronomy.
   - Suggest likely causes, explain how to distinguish them, ask targeted clarifying questions to narrow down the diagnosis, and present evidence-based recommendations.
   - Mention KVK and local extension officers as supportive next-step partners for localized soil/tissue testing, not as an excuse to avoid providing advice.

5. UNDER-SPECIFIED / VAGUE INQUIRY CROSS-QUESTIONING:
   - If the farmer asks an under-specified, broad question without specifying the crop or the specific disease/pest (e.g. "What pesticide should I use?", "What medicine for my plant?", "Which fertilizer should I spray?", "How to treat leaf spots?"):
   - NEVER guess a crop or prescribe random chemicals blindly. Chemical prescription without knowing the crop or pest target is dangerous and unsafe.
   - Politely cross-question the farmer first to gather essential diagnostic information:
     a) Which crop are they growing (e.g. Mango, Coconut, Sugarcane, Tobacco, Rice, or other)?
     b) What exact symptoms or damage are they seeing (e.g. black spots, yellowing, wilting, powder, holes, insects)?
     c) Which plant parts are affected (leaves, flowers, fruits, stem)?
   - Guide them on what to inspect, and formulate clear, clickable follow-up options for them to specify their crop and issue.

6. RESPONSE STRUCTURE:
   Format responses with clear, readable markdown sections:
   - **Diagnosis & Potential Causes** (Disease, Pest, or Nutrient Deficiency)
   - **Key Symptoms to Check** (Differentiating features)
   - **Immediate Cultural & Organic Management** (Safe first actions)
   - **Chemical Treatment (If Severity Exceeds Threshold)** (Safe, approved options with exact dosage)
   - **Important Safety & Pollinator Advisory**
   
   At the very end of your response, output:
   FOLLOW_UP_QUESTIONS:
   - Question 1 (e.g. asking about growth stage, crop, or severity)
   - Question 2 (e.g. asking about specific pattern or symptom location)
"""

INTENT_PROMPT = """You are an intent classification system for an agricultural chatbot.
Classify the following user query into one of two categories:
1. "AGRICULTURAL": The query is about farming, crops, plants, pests, diseases, fertilizers, nutrients, soil, harvesting, agronomy, livestock, weather, or agriculture (even if it is about crops outside our core database, e.g., Tomato, Cotton, Wheat, Potato, Chilli, Apple, etc.).
2. "NON_AGRICULTURAL": The query is completely unrelated to farming or agriculture (e.g., coding, cryptocurrency, finance, entertainment, general chat, movies, politics, math, etc.).

Query: "{query}"

Output ONLY a valid JSON object in this exact format:
{{"is_agricultural": true, "crop": "detected_crop_or_general", "topic": "pest/disease/nutrient/cultivation/general"}}
"""

WEB_FALLBACK_PROMPT = """You are AgriBot, an expert agricultural advisory assistant.
The farmer asked an agricultural question that is outside our primary pre-indexed crops (Mango, Coconut, Sugarcane, Tobacco, Rice).

Farmer's Question: "{query}"
Detected Crop/Topic: "{crop}"

Provide an authoritative, grounded agricultural advisory following Indian agricultural university standards (ICAR / State Agricultural Universities / Vikaspedia).
Rules:
1. Check for nutrient deficiencies as well as pest/disease causes.
2. Recommend cultural & organic controls first.
3. NEVER recommend banned pesticides in India (e.g., NEVER recommend Phosphamidon, Monocrotophos, Endosulfan, Methyl Parathion).
4. For critical chemicals, ask diagnostic questions regarding stage and severity before heavy application.

Structure your response cleanly:
1. **Diagnosis & Overview**
2. **Cultural & Preventive Measures**
3. **Chemical & Organic Management** (cite precise standard dosages if applicable, e.g. ml/L, kg/ha)
4. **Important Safety & Pollinator Advisory**

At the end of your response, output two sections:
SOURCES:
- Source Name (e.g., ICAR / TNAU / Vikaspedia / Department of Agriculture)
FOLLOW_UP_QUESTIONS:
- Suggested diagnostic question 1 (e.g. growth stage, severity)
- Suggested diagnostic question 2 (e.g. symptom location)
"""

class GeminiGenerator:
    """
    RAG LLM generator powered by Google Gemini with:
    1. Local Vector DB RAG for core crops.
    2. Dynamic Intent Classification for low-confidence queries.
    3. Live Agricultural Knowledge Fallback & Auto-Ingestion for unsupported crops.
    4. Polite rejection for non-agricultural queries.
    """
    def __init__(self, env_path=None, model_name=None):
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
        configured_model = os.getenv("LLM_MODEL")
        self.model_name = model_name or configured_model or "gemini-flash-latest"

    @staticmethod
    def _extract_response_text(response) -> str:
        """Safely extracts text from Gemini response, avoiding ValueError if finish_reason != STOP or text quick accessor fails."""
        try:
            if hasattr(response, "text") and response.text:
                return response.text.strip()
        except Exception:
            pass
            
        try:
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    parts_text = []
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            parts_text.append(part.text)
                    if parts_text:
                        return "".join(parts_text).strip()
        except Exception:
            pass
            
        return ""

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
                    generation_config={"temperature": 0.0, "max_output_tokens": 1024},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                text = self._extract_response_text(res)
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

    def analyze_crop_image(self, image: Any, user_text: str = None) -> dict:
        """
        Uses Gemini Multimodal Vision to inspect the uploaded plant/leaf image.
        Returns:
            - detected_crop: e.g. 'mango', 'rice', 'coconut', 'sugarcane', 'tobacco'
            - visual_symptoms: description of visual lesions/spots/insects/damage
            - likely_problem: disease/pest/nutrient deficiency name
            - search_query: search terms for agricultural vector database retrieval
        """
        prompt = (
            "You are an expert agricultural plant pathologist and entomologist. "
            "Examine this crop leaf/plant photo closely.\n"
            f"Farmer's query: '{user_text or ''}'\n\n"
            "Analyze the image and return ONLY a valid JSON object in this exact format:\n"
            "{\n"
            '  "detected_crop": "mango/coconut/sugarcane/tobacco/rice/or specific plant name",\n'
            '  "visual_symptoms": "short 1-2 sentence description of visual lesions/spots/damage",\n'
            '  "likely_problem": "disease, pest, or nutrient deficiency name",\n'
            '  "search_query": "3-5 key search terms for vector knowledge retrieval"\n'
            "}"
        )
        attempts = 0
        total_keys = len(self.api_keys)
        while attempts < total_keys:
            key_idx = (self.current_key_idx + attempts) % total_keys
            try:
                self._configure_key(key_idx)
                model = genai.GenerativeModel(model_name=self.model_name)
                res = model.generate_content(
                    [image, prompt],
                    generation_config={"temperature": 0.1, "max_output_tokens": 1024},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                text = self._extract_response_text(res)
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
                break
            except Exception:
                attempts += 1
        return {
            "detected_crop": "general",
            "visual_symptoms": "Visible plant foliage abnormalities",
            "likely_problem": "Crop disorder",
            "search_query": user_text or "crop disease diagnosis"
        }

    def generate_web_fallback(self, query: str, crop: str = "general", history: list = None, image: Any = None) -> dict:
        """Generates grounded agricultural advisory for queries not present in local vector DB."""
        history_block = ""
        if history:
            formatted_turns = []
            for turn in history[-6:]:
                role = "Farmer" if turn.get("role") in ["user", "farmer"] else "AgriBot"
                content = (turn.get("content") or "").strip()
                if content:
                    if len(content) > 350:
                        content = content[:350] + "..."
                    formatted_turns.append(f"{role}: {content}")
            if formatted_turns:
                history_block = "Recent Conversation History:\n" + "\n".join(formatted_turns) + "\n\n"

        image_prompt_note = ""
        if image:
            image_prompt_note = (
                "\nPHOTO ATTACHED BY FARMER:\n"
                "The farmer uploaded a photo of the plant. Inspect the visual symptoms in the image carefully and integrate your observations into the advisory.\n\n"
            )

        attempts = 0
        total_keys = len(self.api_keys)
        while attempts < total_keys:
            key_idx = (self.current_key_idx + attempts) % total_keys
            try:
                self._configure_key(key_idx)
                model = genai.GenerativeModel(model_name=self.model_name)
                prompt = (
                    f"{history_block}{image_prompt_note}" +
                    WEB_FALLBACK_PROMPT.format(query=query, crop=crop or "General Agriculture")
                )
                content_input = [image, prompt] if image else prompt
                response = model.generate_content(
                    content_input,
                    generation_config={"temperature": 0.2, "top_p": 0.85, "max_output_tokens": 8192},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                raw_text = self._extract_response_text(response)
                if not raw_text:
                    raise ValueError("Empty response received from LLM")

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

    def generate_rag_answer(self, query: str, context_chunks: list, crop: str = None, history: list = None, image: Any = None) -> dict:
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
            return self.generate_web_fallback(query=query, crop=detected_crop, history=history, image=image)

        # Format conversation history if provided
        history_block = ""
        if history:
            formatted_turns = []
            for turn in history[-6:]:
                role = "Farmer" if turn.get("role") in ["user", "farmer"] else "AgriBot"
                content = (turn.get("content") or "").strip()
                if content:
                    if len(content) > 350:
                        content = content[:350] + "..."
                    formatted_turns.append(f"{role}: {content}")
            if formatted_turns:
                history_block = "Recent Conversation History:\n" + "\n".join(formatted_turns) + "\n\n"

        photo_notes = ""
        if image:
            photo_notes = (
                "\nPHOTO ATTACHED BY FARMER:\n"
                "The farmer uploaded a photo of the crop/leaf. Examine the photo carefully, describe the visible lesions, spots, or pest damage you observe, and synthesize your diagnosis using both the image and verified agricultural context.\n\n"
            )

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

        prompt = f"""{history_block}{photo_notes}Farmer's Current Question: {query}
Crop Context: {crop if crop else 'Auto-detected / Multi-crop'}

Verified Context from Agricultural Knowledge Base:
\"\"\"
{combined_context}
\"\"\"

Please provide a well-structured, clear, actionable response based on the above verified context, addressing the farmer's question in the context of the ongoing conversation. 
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
                content_input = [image, prompt] if image else prompt
                response = model.generate_content(
                    content_input,
                    generation_config={"temperature": 0.2, "top_p": 0.85, "max_output_tokens": 8192},
                    request_options={"retry": None}
                )
                self.current_key_idx = key_idx
                raw_text = self._extract_response_text(response)
                if not raw_text:
                    raise ValueError("Empty response received from LLM")
                
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

        excerpt = context_chunks[0].get("payload", {}).get("text", "")[:800] if context_chunks else ""
        friendly_fallback = (
            "Here is the verified agricultural advisory from our knowledge base for your inquiry:\n\n"
            f"{excerpt}\n\n"
            "---\n"
            "**Recommended Diagnostic Steps:**\n"
            "- Inspect the plant to observe whether symptoms are concentrated on older leaves, young flushes, or fruits.\n"
            "- Check for any visible fungal signs (black dots/acervuli), webbing, or sap-sucking insects under the leaves.\n"
            "- Review recent fertilizer and irrigation schedules before applying chemical treatments."
        )
        return {
            "answer": friendly_fallback,
            "crop": crop,
            "confidence": confidence,
            "sources": sources[:3],
            "suggested_questions": [
                "What is the current growth stage of your crop?",
                "Are the symptoms visible across the entire tree or only on specific branches?",
                "Have you applied any fertilizer or fungicide sprays recently?"
            ],
            "should_auto_ingest": False
        }
