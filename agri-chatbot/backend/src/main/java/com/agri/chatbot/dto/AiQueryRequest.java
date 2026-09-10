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
