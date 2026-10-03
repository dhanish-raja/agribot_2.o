import os
from typing import Optional, List, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from embeddings.embedder import GeminiEmbedder
from rag.qdrant_service import QdrantService
from rag.generator import GeminiGenerator
from sarvam.sarvam_service import SarvamService

# Load environment configuration
ai_service_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(ai_service_dir, ".."))
env_path = os.path.join(ai_service_dir, ".env")
qdrant_storage = os.path.join(project_root, "data", "qdrant_storage")

load_dotenv(env_path)
qdrant_url = os.getenv("QDRANT_URL")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agri Chatbot AI & Voice Search Service",
    description="Vector database RAG retrieval, Gemini generation, and Sarvam AI Multilingual Speech Services for Agribot 2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
embedder: Optional[GeminiEmbedder] = None
qdrant: Optional[QdrantService] = None
generator: Optional[GeminiGenerator] = None
sarvam: Optional[SarvamService] = None

@app.on_event("startup")
def startup_event():
    global embedder, qdrant, generator, sarvam
    print("[AI-Service] Initializing GeminiEmbedder, QdrantService, GeminiGenerator & SarvamService...")
    embedder = GeminiEmbedder(env_path=env_path, output_dimensionality=768)
    qdrant = QdrantService(
        collection_name="agri_knowledge",
        vector_dim=768,
        storage_path=qdrant_storage if not qdrant_url or not qdrant_url.startswith("http") else None,
        url=qdrant_url if qdrant_url and qdrant_url.startswith("http") else None
    )
    generator = GeminiGenerator(env_path=env_path)
    sarvam = SarvamService(api_key=os.getenv("SARVAM_AI_API_KEY"))
    print(f"[AI-Service] Services ready. Qdrant indexed with {qdrant.count()} total vectors.")

@app.on_event("shutdown")
def shutdown_event():
    global qdrant
    if qdrant:
        qdrant.close()

# Request & Response Models
class QueryRequest(BaseModel):
    query: str
    crop: Optional[str] = None
    topic: Optional[str] = None
    topK: int = 5

class RetrievalHit(BaseModel):
    id: str
    score: float
    payload: dict

class QueryResponse(BaseModel):
    crop: Optional[str]
    query: str
    total_hits: int
    results: List[RetrievalHit]

class ChatRequest(BaseModel):
    message: Optional[str] = None
    query: Optional[str] = None
    crop: Optional[str] = None
    topic: Optional[str] = None
    topK: int = 4
    sessionId: Optional[str] = None
    language: Optional[str] = None
    enable_audio: bool = False

class ChatResponse(BaseModel):
    answer: str
    crop: Optional[str] = None
    confidence: str
    sources: List[dict] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    audio_base64: Optional[str] = None
    detected_language: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "en-IN"
    speaker: Optional[str] = "kavya"

class STTResponse(BaseModel):
    transcript: str
    english_query: str
    detected_language: str

@app.get("/health")
def health_check():
    vector_count = qdrant.count() if qdrant else 0
    return {
        "status": "UP",
        "service": "ai-service",
        "collection": "agri_knowledge",
        "total_vectors": vector_count,
        "crops": ["mango", "coconut", "sugarcane", "tobacco", "rice"],
        "speech_service": "Sarvam AI (Saaras + Bulbul + Translate)" if sarvam else "Disabled"
    }

# ==============================================================================
# Sarvam AI Speech-to-Text & Text-to-Speech Dedicated Endpoints
# ==============================================================================

@app.post("/speech/stt", response_model=STTResponse)
async def speech_to_text_endpoint(
    file: UploadFile = File(...),
    model: str = Form("saaras:v3")
):
    """Transcribes farmer speech audio and returns transcript + English translation + detected language."""
    if not sarvam:
        raise HTTPException(status_code=503, detail="Sarvam Speech service not initialized.")
    
    audio_bytes = await file.read()
    stt_res = sarvam.speech_to_text(audio_bytes, filename=file.filename or "audio.wav", model=model)
    transcript = stt_res.get("transcript", "")
    lang = stt_res.get("language_code", "en-IN")

    english_query = transcript
    if lang != "en-IN" and transcript:
        try:
            english_query = sarvam.translate(transcript, source_language_code=lang, target_language_code="en-IN")
        except Exception as e:
            print(f"[STT Translation Warning] {e}")

    return STTResponse(
        transcript=transcript,
        english_query=english_query,
        detected_language=lang
    )

@app.post("/speech/tts")
def text_to_speech_endpoint(req: TTSRequest):
    """Synthesizes human-sounding Indian regional voice audio (base64 WAV) using Sarvam Bulbul:v3."""
    if not sarvam:
        raise HTTPException(status_code=503, detail="Sarvam Speech service not initialized.")
    
    lang = req.language_code or "en-IN"
    audio_b64 = sarvam.text_to_speech(req.text, target_language_code=lang, speaker=req.speaker or "kavya")
    if not audio_b64:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech audio from Sarvam AI.")
    
    return {
        "audio_base64": audio_b64,
        "language_code": lang
    }

# ==============================================================================
# Full Multimodal RAG Chat Endpoint (Flowchart Parity with User Architecture)
# ==============================================================================

@app.post("/rag/generate", response_model=ChatResponse)
@app.post("/rag/chat", response_model=ChatResponse)
def rag_chat(request: ChatRequest):
    """
    Multimodal RAG chat implementation conforming to the Agricultural Chatbot Architecture:
    1. Language Detection (Unicode script analyzer / Sarvam)
    2. Translation to English if Non-English
    3. Retrieval from Vector DB & Grounded Generation
    4. Auto-Ingestion into Qdrant for Out-of-DB queries
    5. Translation back to farmer's native language L
    6. Text-to-Speech synthesis in L via Sarvam Bulbul:v3 if requested
    """
    if not embedder or not qdrant or not generator:
        raise HTTPException(status_code=503, detail="AI services not yet fully initialized.")
        
    raw_user_query = request.query or request.message
    if not raw_user_query or not raw_user_query.strip():
        raise HTTPException(status_code=400, detail="Query or message text is required.")

    raw_user_query = raw_user_query.strip()
    
    # Step 1: Language Detection
    detected_lang = request.language
    if not detected_lang and sarvam:
        detected_lang = sarvam.detect_script_language(raw_user_query)
    if not detected_lang:
        detected_lang = "en-IN"

    # Step 2: Translate to English if Non-English
    query_for_rag = raw_user_query
    if detected_lang != "en-IN" and sarvam:
        try:
            query_for_rag = sarvam.translate(raw_user_query, source_language_code=detected_lang, target_language_code="en-IN")
            print(f"[Language Pipeline] '{raw_user_query}' ({detected_lang}) -> '{query_for_rag}' (en-IN)")
        except Exception as trans_err:
            print(f"[Translation to English Warning] {trans_err}")

    # Auto-detect crop if not explicitly passed
    crop_filter = request.crop.lower().strip() if request.crop else None
    if not crop_filter:
        for c in ["mango", "coconut", "sugarcane", "tobacco", "rice"]:
            if c in query_for_rag.lower() or c in raw_user_query.lower():
                crop_filter = c
                break

    try:
        # Step 3: Embed Query in English
        query_vec = embedder.embed_texts([query_for_rag], task_type="retrieval_query")[0]
        
        # Step 4: Retrieve from Qdrant Vector DB
        hits = qdrant.search(
            query_vector=query_vec,
            crop=crop_filter,
            topic=request.topic,
            top_k=request.topK
        )
        
        # Step 5: Grounded Gemini generation with 3-tier routing
        res = generator.generate_rag_answer(query=query_for_rag, context_chunks=hits, crop=crop_filter)
        english_answer = res.get("answer", "")

        # Step 6: Auto-ingest new agricultural knowledge if synthesized dynamically
        if res.get("should_auto_ingest") and res.get("content_to_ingest"):
            try:
                ingest_crop = res.get("crop", "general")
                new_record = {
                    "crop": ingest_crop,
                    "topic": "Live Verified Advisory",
                    "content": res["content_to_ingest"],
                    "source": "AgriBot Live Knowledge Ingestion",
                    "source_url": "https://icar.org.in"
                }
                new_vec = embedder.embed_texts([res["content_to_ingest"][:1000]], task_type="retrieval_document")
                if new_vec:
                    qdrant.upsert_records([new_record], new_vec)
                    print(f"[Auto-Ingest] Cached new knowledge for '{ingest_crop}' into Qdrant!")
            except Exception as ingest_err:
                print(f"[Auto-Ingest Warning] Could not cache to Qdrant: {ingest_err}")

        # Step 7: Translate response back to farmer's language L
        final_answer = english_answer
        if detected_lang != "en-IN" and sarvam:
            try:
                final_answer = sarvam.translate(english_answer, source_language_code="en-IN", target_language_code=detected_lang)
            except Exception as trans_back_err:
                print(f"[Translation Back Warning] {trans_back_err}")

        # Step 8: Text-to-Speech synthesis in language L via Sarvam Bulbul
        audio_b64 = None
        if request.enable_audio and sarvam:
            try:
                audio_b64 = sarvam.text_to_speech(final_answer, target_language_code=detected_lang, speaker="kavya")
            except Exception as tts_err:
                print(f"[TTS Synthesis Warning] {tts_err}")

        clean_res = {
            "answer": final_answer,
            "crop": res.get("crop"),
            "confidence": res.get("confidence", "Medium"),
            "sources": res.get("sources", []),
            "suggested_questions": res.get("suggested_questions", []),
            "audio_base64": audio_b64,
            "detected_language": detected_lang
        }
        return ChatResponse(**clean_res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/rag/voice-chat", response_model=ChatResponse)
async def rag_voice_chat(
    file: UploadFile = File(...),
    crop: Optional[str] = Form(None),
    language: Optional[str] = Form(None)
):
    """
    Complete Voice-to-Voice pipeline:
    Microphone Audio -> Sarvam STT -> Translation -> Qdrant RAG -> Sarvam TTS -> Audio + Text
    """
    if not sarvam:
        raise HTTPException(status_code=503, detail="Sarvam Speech service not initialized.")
    
    audio_bytes = await file.read()
    stt_res = sarvam.speech_to_text(audio_bytes, filename=file.filename or "audio.wav")
    transcript = stt_res.get("transcript", "")
    detected_lang = language or stt_res.get("language_code", "en-IN")

    if not transcript:
        raise HTTPException(status_code=400, detail="Could not detect clear speech from audio.")

    # Execute RAG chat with enable_audio=True
    chat_req = ChatRequest(
        message=transcript,
        crop=crop,
        language=detected_lang,
        enable_audio=True
    )
    return rag_chat(chat_req)

@app.post("/rag/query", response_model=QueryResponse)
def rag_query(request: QueryRequest):
    if not embedder or not qdrant:
        raise HTTPException(status_code=503, detail="Vector search service not yet initialized.")
        
    try:
        query_vec = embedder.embed_texts([request.query], task_type="retrieval_query")[0]
        hits = qdrant.search(
            query_vector=query_vec,
            crop=request.crop,
            topic=request.topic,
            top_k=request.topK
        )
        return QueryResponse(
            crop=request.crop,
            query=request.query,
            total_hits=len(hits),
            results=[RetrievalHit(id=str(h["id"]), score=h["score"], payload=h["payload"]) for h in hits]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
def generate_embedding(text: str):
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedder not initialized.")
    vec = embedder.embed_texts([text], task_type="retrieval_query")[0]
    return {"text": text, "dimension": len(vec), "embedding": vec}

@app.post("/cv/predict")
def cv_predict():
    return {"status": "Pending CV model integration in Step 5"}
