package com.agri.chatbot.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Farmer query payload")
public class ChatRequest {
    
    @Schema(description = "Natural language message or query from the farmer", example = "How to control bacterial blight in rice?")
    private String message;
    
    @Schema(description = "Specific crop context filter ('mango', 'coconut', 'sugarcane', 'tobacco', 'rice')", example = "rice")
    private String crop;
    
    @Schema(description = "Unique user session identifier for tracking conversation history", example = "session-farmer-101")
    private String sessionId;
    
    @Schema(description = "Recent conversation turns for multi-turn context")
    private java.util.List<java.util.Map<String, Object>> history;
    
    @Schema(description = "Base64 encoded image string for visual leaf/crop diagnosis")
    private String image;
    
    private String image_base64;
}
