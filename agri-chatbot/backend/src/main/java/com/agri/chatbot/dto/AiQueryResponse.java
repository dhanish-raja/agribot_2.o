package com.agri.chatbot.dto;

import java.util.List;
import java.util.Map;
import lombok.Data;

@Data
public class AiQueryResponse {
    private List<Map<String, Object>> results;
}
