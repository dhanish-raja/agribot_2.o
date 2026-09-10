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
