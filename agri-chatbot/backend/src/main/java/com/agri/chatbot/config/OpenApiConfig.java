package com.agri.chatbot.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Value("${server.port:8080}")
    private String serverPort;

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("AgriBot 2.0 Backend Gateway API")
                .version("2.0.0")
                .description("Production Spring Boot 3 Gateway API for AgriBot 2.0. Routes farmer chat requests to the Python FastAPI RAG microservice and Qdrant vector database (1,514 vectors across Mango, Coconut, Sugarcane, Tobacco, and Rice).")
                .contact(new Contact()
                    .name("AgriBot Engineering Team")
                    .url("https://github.com/dhanish-raja/agribot_2.o"))
                .license(new License().name("Apache 2.0").url("http://springdoc.org")))
            .servers(List.of(
                new Server().url("http://localhost:" + serverPort).description("Local Gateway Server"),
                new Server().url("http://localhost:8000").description("Direct AI Service Engine (FastAPI)")
            ));
    }
}
