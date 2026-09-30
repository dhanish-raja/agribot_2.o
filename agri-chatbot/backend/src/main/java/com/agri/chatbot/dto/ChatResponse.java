package com.agri.chatbot.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Agricultural advisory response with citations and follow-up queries")
public class ChatResponse {
    
    @Schema(description = "Grounded advisory answer generated from the knowledge base", example = "Bacterial blight in rice can be managed by avoiding excess nitrogen...")
    private String answer;
    
    @Schema(description = "List of verified knowledge sources and similarity match scores")
    private List<String> sources;
    
    @Schema(description = "Visual prediction diagnosis (Reserved for Step 5 CV)", example = "bacterial_leaf_blight")
    private String prediction;
    
    @Schema(description = "Identified or filtered crop", example = "rice")
    private String crop;
    
    @Schema(description = "Retrieval confidence level based on vector cosine similarity", example = "High")
    private String confidence;
    
    @Schema(description = "Helpful follow-up questions tailored to the disease or crop practice")
    private List<String> suggestedQuestions;

    public ChatResponse(String answer, List<String> sources, String prediction) {
        this.answer = answer;
        this.sources = sources;
        this.prediction = prediction;
    }
}
