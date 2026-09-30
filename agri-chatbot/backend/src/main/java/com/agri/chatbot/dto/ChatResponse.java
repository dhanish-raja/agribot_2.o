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
    private String crop;
    private String confidence;
    private List<String> suggestedQuestions;

    public ChatResponse(String answer, List<String> sources, String prediction) {
        this.answer = answer;
        this.sources = sources;
        this.prediction = prediction;
    }
}
