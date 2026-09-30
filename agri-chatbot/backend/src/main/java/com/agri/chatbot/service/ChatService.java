package com.agri.chatbot.service;

import com.agri.chatbot.dto.ChatRequest;
import com.agri.chatbot.dto.ChatResponse;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class ChatService {

    private final AiServiceClient aiServiceClient;

    public ChatService(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    @SuppressWarnings("unchecked")
    public ChatResponse processChat(ChatRequest request) {
        Map<String, Object> aiResult = aiServiceClient.generateChat(
            request.getMessage(),
            request.getCrop(),
            request.getSessionId()
        );
        
        String answer = (String) aiResult.getOrDefault("answer", "No response generated.");
        String crop = (String) aiResult.get("crop");
        String confidence = (String) aiResult.getOrDefault("confidence", "Medium");
        
        List<String> sourcesList = new ArrayList<>();
        Object sourcesObj = aiResult.get("sources");
        if (sourcesObj instanceof List<?>) {
            for (Object item : (List<?>) sourcesObj) {
                if (item instanceof Map<?, ?>) {
                    Map<?, ?> smap = (Map<?, ?>) item;
                    sourcesList.add(String.format("%s | %s (Score: %s)", smap.get("crop"), smap.get("topic"), smap.get("similarity_score")));
                } else if (item != null) {
                    sourcesList.add(item.toString());
                }
            }
        }

        List<String> suggestedQuestions = new ArrayList<>();
        Object suggObj = aiResult.get("suggested_questions");
        if (suggObj instanceof List<?>) {
            for (Object q : (List<?>) suggObj) {
                if (q != null) suggestedQuestions.add(q.toString());
            }
        }
        
        return new ChatResponse(
            answer,
            sourcesList,
            null,
            crop,
            confidence,
            suggestedQuestions
        );
    }
}
