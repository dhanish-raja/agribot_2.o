package com.agri.chatbot.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
@RequestMapping("/api")
@Tag(name = "System Health & Monitoring", description = "Endpoints for liveness and service readiness checks")
public class HealthController {

    @GetMapping("/health")
    @Operation(summary = "Check backend gateway health", description = "Returns UP status and service identifiers")
    public Map<String, String> health() {
        return Map.of("status", "UP", "service", "agri-backend", "gateway", "spring-boot-3");
    }
}
