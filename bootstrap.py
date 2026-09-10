import os
import json

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot"
os.makedirs(base_dir, exist_ok=True)

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

# 1. Root files
write_file("README.md", """
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
""")

write_file(".env.example", """
BACKEND_PORT=8080
AI_SERVICE_URL=http://ai-service:8000
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=agri_knowledge
""")

write_file("docker-compose.yml", """
version: "3.8"

services:
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - agri-network

  backend:
    build:
      context: ./backend
    ports:
      - "8080:8080"
    environment:
      - AI_SERVICE_URL=http://ai-service:8000
    depends_on:
      - ai-service
    networks:
      - agri-network

  ai-service:
    build:
      context: ./ai-service
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - QDRANT_COLLECTION=agri_knowledge
    depends_on:
      - qdrant
    networks:
      - agri-network

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - agri-network

networks:
  agri-network:
    driver: bridge

volumes:
  qdrant_data:
""")

# 2. AI Service (Python FastAPI)
write_file("ai-service/requirements.txt", """
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
qdrant-client==1.7.0
""")

write_file("ai-service/Dockerfile", """
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

write_file("ai-service/main.py", """
from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="Agri Chatbot AI Service")

class QueryRequest(BaseModel):
    query: str
    crop: str = "mango"
    topK: int = 5

class QueryResponse(BaseModel):
    results: list

@app.get("/health")
def health_check():
    return {"status": "UP", "service": "ai-service"}

@app.post("/rag/query")
def rag_query(request: QueryRequest):
    # TODO: Implement actual RAG retrieval with Qdrant and LLM
    return {
        "results": [
            {
                "text": f"Temporary simulated response for query: {request.query} regarding crop: {request.crop}. Qdrant retrieval and LLM not yet implemented.",
                "metadata": {"source": "temp", "crop": request.crop}
            }
        ]
    }

@app.post("/embed")
def generate_embedding():
    # TODO: Implement embedding generation
    return {"status": "Not implemented"}

@app.post("/cv/predict")
def cv_predict():
    # TODO: Implement CV prediction
    return {"status": "Not implemented"}
""")

for module in ["rag", "embeddings", "ingestion", "crawler", "cv"]:
    write_file(f"ai-service/{module}/__init__.py", "")

# 3. Backend (Spring Boot)
write_file("backend/Dockerfile", """
FROM maven:3.9.5-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
""")

write_file("backend/pom.xml", """
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    <groupId>com.agri</groupId>
    <artifactId>chatbot</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>agri-chatbot</name>
    <description>Backend for Agricultural AI Chatbot</description>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
""")

write_file("backend/src/main/resources/application.properties", """
server.port=${BACKEND_PORT:8080}
ai.service.url=${AI_SERVICE_URL:http://localhost:8000}
""")

write_file("backend/src/main/java/com/agri/chatbot/AgriChatbotApplication.java", """
package com.agri.chatbot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
public class AgriChatbotApplication {
    public static void main(String[] args) {
        SpringApplication.run(AgriChatbotApplication.class, args);
    }
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
""")

write_file("backend/src/main/java/com/agri/chatbot/config/CorsConfig.java", """
package com.agri.chatbot.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS");
    }
}
""")

write_file("backend/src/main/java/com/agri/chatbot/controller/HealthController.java", """
package com.agri.chatbot.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP", "service", "agri-backend");
    }
}
""")

write_file("backend/src/main/java/com/agri/chatbot/dto/ChatRequest.java", """
package com.agri.chatbot.dto;

import lombok.Data;

@Data
public class ChatRequest {
    private String message;
    private String sessionId;
}
""")

write_file("backend/src/main/java/com/agri/chatbot/dto/ChatResponse.java", """
package com.agri.chatbot.dto;

import java.util.List;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatResponse {
    private String answer;
    private List<String> sources;
    private String prediction;
}
""")

write_file("backend/src/main/java/com/agri/chatbot/dto/AiQueryRequest.java", """
package com.agri.chatbot.dto;

import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class AiQueryRequest {
    private String query;
    private String crop;
    private int topK;
}
""")

write_file("backend/src/main/java/com/agri/chatbot/dto/AiQueryResponse.java", """
package com.agri.chatbot.dto;

import java.util.List;
import java.util.Map;
import lombok.Data;

@Data
public class AiQueryResponse {
    private List<Map<String, Object>> results;
}
""")

write_file("backend/src/main/java/com/agri/chatbot/service/AiServiceClient.java", """
package com.agri.chatbot.service;

import com.agri.chatbot.dto.AiQueryRequest;
import com.agri.chatbot.dto.AiQueryResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class AiServiceClient {
    
    private final RestTemplate restTemplate;
    
    @Value("${ai.service.url}")
    private String aiServiceUrl;

    public AiServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public AiQueryResponse queryRag(String query) {
        String url = aiServiceUrl + "/rag/query";
        AiQueryRequest request = new AiQueryRequest(query, "mango", 5);
        try {
            return restTemplate.postForObject(url, request, AiQueryResponse.class);
        } catch (Exception e) {
            AiQueryResponse fallback = new AiQueryResponse();
            fallback.setResults(java.util.List.of(
                java.util.Map.of("text", "Error communicating with AI service: " + e.getMessage())
            ));
            return fallback;
        }
    }
}
""")

write_file("backend/src/main/java/com/agri/chatbot/service/ChatService.java", """
package com.agri.chatbot.service;

import com.agri.chatbot.dto.ChatRequest;
import com.agri.chatbot.dto.ChatResponse;
import com.agri.chatbot.dto.AiQueryResponse;
import org.springframework.stereotype.Service;
import java.util.ArrayList;

@Service
public class ChatService {

    private final AiServiceClient aiServiceClient;

    public ChatService(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    public ChatResponse processChat(ChatRequest request) {
        AiQueryResponse aiResponse = aiServiceClient.queryRag(request.getMessage());
        
        String answer = "Chat service is connected. ";
        if (aiResponse != null && aiResponse.getResults() != null && !aiResponse.getResults().isEmpty()) {
            answer += aiResponse.getResults().get(0).get("text");
        }
        
        return new ChatResponse(answer, new ArrayList<>(), null);
    }
}
""")

write_file("backend/src/main/java/com/agri/chatbot/controller/ChatController.java", """
package com.agri.chatbot.controller;

import com.agri.chatbot.dto.ChatRequest;
import com.agri.chatbot.dto.ChatResponse;
import com.agri.chatbot.service.ChatService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping("/chat")
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return chatService.processChat(request);
    }
}
""")

# 4. Frontend (React)
write_file("frontend/Dockerfile", """
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
""")

write_file("frontend/package.json", """
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port 3000",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
""")

write_file("frontend/tsconfig.json", """
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""")

write_file("frontend/tsconfig.node.json", """
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
""")

write_file("frontend/vite.config.ts", """
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000
  }
})
""")

write_file("frontend/index.html", """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agri Chatbot</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

write_file("frontend/src/main.tsx", """
import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""")

write_file("frontend/src/index.css", """
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body {
  font-family: Arial, sans-serif;
  background-color: #f4f7f6;
  color: #333;
}
""")

write_file("frontend/src/App.tsx", """
import { useState } from "react"
import "./App.css"

interface Message {
  text: string;
  sender: "user" | "assistant";
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hello! I am your agricultural assistant. How can I help you today?", sender: "assistant" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    setMessages(prev => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8080/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, sessionId: "test-session" })
      });
      
      if (!response.ok) throw new Error("Network response was not ok");
      
      const data = await response.json();
      setMessages(prev => [...prev, { text: data.answer, sender: "assistant" }]);
    } catch (err: any) {
      setError(err.message || "Error connecting to the server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Agricultural AI Assistant</h1>
      </header>
      
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="message assistant loading">Typing...</div>}
        {error && <div className="error-message">Error: {error}</div>}
      </div>

      <div className="chat-input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask a question about your crops..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}

export default App
""")

write_file("frontend/src/App.css", """
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.chat-header {
  background: #2e7d32;
  color: white;
  padding: 1rem;
  text-align: center;
}

.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  padding: 0.8rem 1rem;
  border-radius: 8px;
  max-width: 80%;
  line-height: 1.4;
}

.message.user {
  background: #e3f2fd;
  align-self: flex-end;
  border-bottom-right-radius: 0;
}

.message.assistant {
  background: #f5f5f5;
  align-self: flex-start;
  border-bottom-left-radius: 0;
}

.loading {
  color: #666;
  font-style: italic;
}

.error-message {
  color: #d32f2f;
  text-align: center;
  margin: 0.5rem 0;
}

.chat-input-area {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #ddd;
  gap: 0.5rem;
}

.chat-input-area input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.chat-input-area button {
  padding: 0.8rem 1.5rem;
  background: #2e7d32;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.chat-input-area button:disabled {
  background: #9e9e9e;
}
""")

for d in ["data/raw", "data/processed", "data/manifests", "models", "scripts", "docs"]:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    write_file(f"{d}/.gitkeep", "")

print("Bootstrap completed.")
