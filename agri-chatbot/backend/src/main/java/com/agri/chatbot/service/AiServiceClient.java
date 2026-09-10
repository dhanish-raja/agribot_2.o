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
