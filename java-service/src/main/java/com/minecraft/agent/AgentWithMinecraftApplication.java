package com.minecraft.agent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@SpringBootApplication
@RestController
public class AgentWithMinecraftApplication {

    public static void main(String[] args) {
        SpringApplication.run(AgentWithMinecraftApplication.class, args);
    }

    @GetMapping("/health")
    public Map<String,Object> health() {
        return Map.of(
                "service","agentWithMinecraft",
                "status","UP",
                "timestamp",System.currentTimeMillis()
        );
    }
}
