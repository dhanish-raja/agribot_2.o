FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY agri-chatbot/ai-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and vector database data
COPY agri-chatbot/ai-service/ ./agri-chatbot/ai-service/
COPY agri-chatbot/data/ ./agri-chatbot/data/

WORKDIR /app/agri-chatbot/ai-service

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
