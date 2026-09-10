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
