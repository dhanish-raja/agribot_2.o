package com.agri.chatbot.service;

import com.agri.chatbot.dto.AiQueryRequest;
import com.agri.chatbot.dto.AiQueryResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiServiceClient {
    
    private final RestTemplate restTemplate;
    
    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceUrl;

    public AiServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> generateChat(String message, String crop, String sessionId) {
        String url = aiServiceUrl + "/rag/chat";
        Map<String, Object> request = new HashMap<>();
        request.put("message", message);
        if (crop != null && !crop.isBlank()) {
            request.put("crop", crop.trim().toLowerCase());
        }
        if (sessionId != null && !sessionId.isBlank()) {
            request.put("sessionId", sessionId.trim());
        }

        try {
            return restTemplate.postForObject(url, request, Map.class);
        } catch (Exception e) {
            Map<String, Object> fallback = new HashMap<>();
            fallback.put("answer", "Unable to communicate with AgriBot AI Service: " + e.getMessage());
            fallback.put("confidence", "Low");
            fallback.put("sources", Collections.emptyList());
            fallback.put("suggested_questions", Collections.emptyList());
            return fallback;
        }
    }

    public AiQueryResponse queryRag(String query, String crop) {
        String url = aiServiceUrl + "/rag/query";
        AiQueryRequest request = new AiQueryRequest(query, crop, 5);
        try {
            return restTemplate.postForObject(url, request, AiQueryResponse.class);
        } catch (Exception e) {
            AiQueryResponse fallback = new AiQueryResponse();
            fallback.setResults(List.of(
                Map.of("text", "Error communicating with AI service: " + e.getMessage())
            ));
            return fallback;
        }
    }
}
