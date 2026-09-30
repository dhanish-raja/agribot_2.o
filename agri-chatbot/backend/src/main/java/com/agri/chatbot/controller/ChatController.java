package com.agri.chatbot.controller;

import com.agri.chatbot.dto.ChatRequest;
import com.agri.chatbot.dto.ChatResponse;
import com.agri.chatbot.service.ChatService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@Tag(name = "Agricultural Chat & RAG", description = "Endpoints for farmer natural language advisory, crop diagnostics, and RAG retrieval")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping("/chat")
    @Operation(
        summary = "Process farmer crop question via RAG",
        description = "Accepts a natural language query with optional crop filter ('mango', 'coconut', 'sugarcane', 'tobacco', 'rice') and returns a grounded answer with citations and follow-up questions."
    )
    @ApiResponses(value = {
        @ApiResponse(
            responseCode = "200", 
            description = "Successful advisory response generated from vector DB",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ChatResponse.class))
        ),
        @ApiResponse(responseCode = "500", description = "Internal gateway or AI microservice error")
    })
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return chatService.processChat(request);
    }
}
