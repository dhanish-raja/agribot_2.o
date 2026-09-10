# Agricultural AI Chatbot

## 1. Project overview
This is a web-based AI agricultural assistant that answers farmer questions. It uses React for the frontend, Spring Boot for the backend, Python FastAPI for AI/RAG services, and Qdrant as the vector database.

## 2. Architecture diagram
React
   |
Spring Boot
   |
Python FastAPI
   |
Qdrant

## 3. Prerequisites
- Docker & Docker Compose
- Java 17+ (optional, for local development)
- Python 3.10+ (optional, for local development)
- Node.js 18+ (optional, for local development)

## 4. How to run locally
- cd frontend && npm install && npm run dev
- cd backend && mvn spring-boot:run
- cd ai-service && pip install -r requirements.txt && uvicorn main:app --reload
- Run Qdrant locally

## 5. How to run using Docker Compose
```bash
docker compose up --build
```

## 6. Backend URL
http://localhost:8080

## 7. AI service URL
http://localhost:8000

## 8. Qdrant URL
http://localhost:6333

## 9. Available health endpoints
- Backend: http://localhost:8080/api/health
- AI Service: http://localhost:8000/health

## 10. Current implementation status
Step 1 complete: Project foundation is established. React, Spring Boot, FastAPI, and Qdrant are connected.

## 11. Future implementation steps
- Step 2: Data pipeline and ingestion
- Step 3: RAG and LLM integration
- Step 4: Image CV integration
