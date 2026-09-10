# Agribot 2.0: AI-Powered Agricultural Assistant & Knowledge Platform

> A production-ready, full-stack agricultural decision support platform built for farmers. It combines an adaptive multi-format web and document crawler, structured factual knowledge extraction powered by Gemini, high-dimensional vector search with Qdrant, and an interactive full-stack chat interface.

---

## 🌾 Project Vision & Overview
Agribot 2.0 is designed to bridge the gap between complex agricultural science and actionable farmer advisory. Agricultural information in India and globally is distributed across diverse formats: static agronomy portals, university tables (TNAU, ICAR), interactive modal-based web applications, research publications, and PDF package of practices.

Agribot 2.0 ingests, validates, segments, and indexes this multi-modal data into structured, source-grounded knowledge objects—ensuring zero hallucination, strict adherence to scientific agronomy, and high-accuracy retrieval.

---

## 🏗️ System Architecture

`mermaid
graph TD
    User([Farmer / Agronomist]) <--> ReactUI[React + TypeScript Frontend]
    ReactUI <--> SpringBoot[Spring Boot 3 Backend Gateway]
    SpringBoot <--> FastAPI[Python FastAPI AI Microservice]
    FastAPI <--> Ingestion[Adaptive Ingestion & Crawler Engine]
    FastAPI <--> Gemini[Google Gemini LLM / Flash]
    FastAPI <--> Qdrant[(Qdrant Vector Database)]
    Ingestion --> Sources[(Agricultural Knowledge Sources)]
`

### Architectural Tiers:
1. **Frontend (gri-chatbot/frontend):** Modern, accessible React 18 + TypeScript + Vite UI designed for farmers to ask natural language crop queries.
2. **Backend Gateway (gri-chatbot/backend):** Spring Boot 3 (Java 17) REST API serving as a secure gateway, managing sessions, CORS, and routing queries to AI microservices.
3. **AI & Ingestion Service (gri-chatbot/ai-service):** Python FastAPI service containing the crawler framework, Gemini-powered factual extractors, Pydantic data validation, and vector database connectors.
4. **Vector Store (Qdrant):** High-speed vector similarity engine running on port 6333 for RAG semantic search.
5. **Container Orchestration (docker-compose.yml):** Unified orchestration configuring all four services with environment isolation and health checks.

---

## 🚀 Accomplishments & Current Status (Steps 1 – 2.6 Complete)

### ✅ Step 1: Core Full-Stack Infrastructure
- Full connectivity verified between React, Spring Boot, FastAPI, and Qdrant.
- Health monitoring endpoints implemented (/api/health, /health).
- Dockerized deployment configured with multi-stage builds.

### ✅ Step 2 & 2.5: Adaptive Data Ingestion Framework
A generalized, resilient ingestion engine capable of processing any agricultural source format:
- **Interactive Web App Crawler (crawl_service.py):**
  - Integrated headless Playwright automation.
  - Automatically identifies hidden DOM elements (modals, accordions, dynamic tabs such as sweetModal).
  - Executes targeted JavaScript DOM manipulations to expose, scrape, and preserve hidden disease symptoms and control practices.
- **Multi-Format Extractor:**
  - **HTML Portals:** Robust markdown transformation stripping navigation noise and boilerplate.
  - **PDF Documents:** Direct pypdf extraction for scientific books and handbooks.
  - **Cloud Drives:** Automatic ID extraction and plaintext export for Google Docs & Google Drive folders.
  - **ICAR Journals:** Intelligent resolution of ePubs and /article/download/ links.
- **Smart Chunking (segmenter.py):**
  - Automatic paragraph and table sub-chunking for long documents (>3,500 chars) to prevent context blowouts and LLM timeouts.
- **Strict Data Validation (alidator.py, cleaner.py):**
  - Enforces rigid Pydantic schemas on every extracted record.
  - Guarantees **0 simulated/hallucinated records**; only source-grounded agricultural facts are committed.

### ✅ Step 2.6: Mango Crop Data Ingestion & Audit
Comprehensive compatibility audit and complete ingestion across **all 34 authoritative Mango sources** (TNAU, ICAR, DHA Multan, National Mango Board, scientific research):
- **32 Sources Successfully Processed:**
  - Complete coverage across diseases (148), pest management (43), cultivation practices (27), physiological disorders (21), varieties (7), harvesting/post-harvest (6), and fertilization (4).
- **297 Verified Knowledge Records** stored in [data/processed/mango/mango_knowledge.jsonl](agri-chatbot/data/processed/mango/mango_knowledge.jsonl).
- **166 Symptom & Disease Images** indexed with source metadata in [data/processed/mango/mango_images.jsonl](agri-chatbot/data/processed/mango/mango_images.jsonl).
- **Audit Tracking:** Comprehensive manifest tracking (manifest.json), duplicate SHA-256 prevention, and snapshot backups stored under data/backups/.

### ✅ Multi-Key Resilience & Quota Management
- Automated API key rotation mechanism supporting unlimited Gemini API keys with dynamic failover on HTTP 429 quota exhaustion.
- Standardized on gemini-flash-latest for zero-friction compatibility across free and paid project tiers.
- Resilient JSON parser supporting strict=False and regex fallback blocks for high-temperature responses.

---

## 📂 Project Directory Structure

`
Agribot_2.o/
├── .gitignore                      # Strict secret & build ignore rules
├── README.md                       # High-level project documentation
├── agri-chatbot/
│   ├── .env.example                # Global environment template
│   ├── docker-compose.yml          # Container configuration for all services
│   ├── ai-service/                 # FastAPI AI & Ingestion Microservice
│   │   ├── .env.example            # AI service API keys template
│   │   ├── Dockerfile
│   │   ├── main.py                 # FastAPI application entrypoint
│   │   ├── requirements.txt
│   │   ├── crawler/                # Multi-format & interactive Playwright crawlers
│   │   │   ├── crawl_service.py
│   │   │   └── interactive_crawler.py
│   │   └── ingestion/              # Extraction, validation, chunking, and quality scripts
│   │       ├── extractor.py        # Multi-key Gemini rotation extractor
│   │       ├── run.py              # Main ingestion runner
│   │       ├── segmenter.py        # Document chunking & table handling
│   │       ├── validator.py        # Pydantic schema validation
│   │       └── quality.py          # Quality audit & verification reporting
│   ├── backend/                    # Spring Boot 3 Java Gateway
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/java/com/agri/chatbot/
│   ├── frontend/                   # React 18 + Vite Frontend
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   └── data/                       # Ingested knowledge base & audit manifests
│       ├── manifests/              # manifest.json (provenance & run stats)
│       ├── processed/              # Verified knowledge JSONL & image datasets
│       │   └── mango/
│       │       ├── mango_knowledge.jsonl (297 records)
│       │       └── mango_images.jsonl    (166 images)
│       ├── raw/                    # Raw crawled snapshots
│       └── sources/                # Target source URLs per crop (mango, coconut, rice, etc.)
└── bootstrap*.py / harden*.py      # Ingestion pipeline bootstrap & test utilities
`

---

## ⚡ Getting Started Locally

### Prerequisites
- Docker & Docker Compose (Recommended)
- Java 17+ (Optional, for backend local run)
- Python 3.10+ (Optional, for AI service local run)
- Node.js 18+ (Optional, for frontend local run)
- Google Gemini API Key

### 1. Clone & Configure Environment
`ash
git clone https://github.com/dhanish-raja/agribot_2.o.git
cd agribot_2.o

# Configure AI Service Environment
cp agri-chatbot/ai-service/.env.example agri-chatbot/ai-service/.env
# Open agri-chatbot/ai-service/.env and add your GEMINI API key(s)
`

### 2. Run with Docker Compose
`ash
cd agri-chatbot
docker compose up --build
`

### 3. Access Services
| Component | Local URL |
| :--- | :--- |
| **Frontend UI** | [http://localhost:3000](http://localhost:3000) |
| **Backend API Gateway** | [http://localhost:8080](http://localhost:8080) |
| **FastAPI AI Service** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Qdrant Dashboard** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |

---

## 🗺️ Roadmap & Next Steps
- [x] **Step 1:** Full-stack foundation & Docker orchestration.
- [x] **Step 2:** Generalized crawler, Playwright interactive scraping, and multi-key Gemini extraction.
- [x] **Step 2.6:** Comprehensive source audit and Mango knowledge base generation (297 records, 166 images).
- [ ] **Step 3 (Current):** Embeddings generation & Qdrant vector indexing.
- [ ] **Step 3.5:** Context-grounded RAG pipeline with verification guardrails.
- [ ] **Step 4:** Expansion to remaining crops (Coconut, Sugarcane, Rice, Tobacco).
- [ ] **Step 5:** Computer Vision (CV) model integration for automated crop disease diagnosis via leaf image uploads.