import os
from typing import Optional, List, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from embeddings.embedder import GeminiEmbedder
from rag.qdrant_service import QdrantService
from rag.generator import GeminiGenerator

# Load environment configuration
ai_service_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(ai_service_dir, ".."))
env_path = os.path.join(ai_service_dir, ".env")
qdrant_storage = os.path.join(project_root, "data", "qdrant_storage")

load_dotenv(env_path)
qdrant_url = os.getenv("QDRANT_URL")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agri Chatbot AI & Vector Search Service",
    description="Vector database RAG retrieval and embedding services for Agribot 2.0"
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

@app.on_event("startup")
def startup_event():
    global embedder, qdrant, generator
    print("[AI-Service] Initializing GeminiEmbedder, QdrantService, & GeminiGenerator...")
    embedder = GeminiEmbedder(env_path=env_path, output_dimensionality=768)
    qdrant = QdrantService(
        collection_name="agri_knowledge",
        vector_dim=768,
        storage_path=qdrant_storage if not qdrant_url or not qdrant_url.startswith("http") else None,
        url=qdrant_url if qdrant_url and qdrant_url.startswith("http") else None
    )
    generator = GeminiGenerator(env_path=env_path)
    print(f"[AI-Service] Qdrant initialized with {qdrant.count()} total vectors across 5 crops.")

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

class ChatResponse(BaseModel):
    answer: str
    crop: Optional[str] = None
    confidence: str
    sources: List[dict] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)

@app.get("/health")
def health_check():
    vector_count = qdrant.count() if qdrant else 0
    return {
        "status": "UP",
        "service": "ai-service",
        "collection": "agri_knowledge",
        "total_vectors": vector_count,
        "crops": ["mango", "coconut", "sugarcane", "tobacco", "rice"]
    }

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

@app.post("/rag/generate", response_model=ChatResponse)
@app.post("/rag/chat", response_model=ChatResponse)
def rag_chat(request: ChatRequest):
    if not embedder or not qdrant or not generator:
        raise HTTPException(status_code=503, detail="AI services not yet fully initialized.")
        
    user_query = request.query or request.message
    if not user_query or not user_query.strip():
        raise HTTPException(status_code=400, detail="Query or message text is required.")

    user_query = user_query.strip()
    
    # Auto-detect crop if not explicitly passed
    crop_filter = request.crop.lower().strip() if request.crop else None
    if not crop_filter:
        for c in ["mango", "coconut", "sugarcane", "tobacco", "rice"]:
            if c in user_query.lower():
                crop_filter = c
                break

    try:
        # Step 1: Embed
        query_vec = embedder.embed_texts([user_query], task_type="retrieval_query")[0]
        
        # Step 2: Retrieve from Qdrant
        hits = qdrant.search(
            query_vector=query_vec,
            crop=crop_filter,
            topic=request.topic,
            top_k=request.topK
        )
        
        # Step 3: Grounded Gemini generation
        res = generator.generate_rag_answer(query=user_query, context_chunks=hits, crop=crop_filter)
        return ChatResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/embed")
def generate_embedding(text: str):
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedder not initialized.")
    vec = embedder.embed_texts([text], task_type="retrieval_query")[0]
    return {"text": text, "dimension": len(vec), "embedding": vec}

@app.post("/cv/predict")
def cv_predict():
    return {"status": "Pending CV model integration in Step 5"}
