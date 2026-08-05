package com.minecraft.agent.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.minecraft.agent.service.RagService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * @program: agentWithMinecraft
 * @description: RAG接口占位
 * @author: pokerjiyin
 * @create: 2026-07-27 22:25
 **/

@RestController
@RequestMapping("/api/rag")
public class RagController {

    private final RagService ragService;

    public RagController(RagService ragService) {
        this.ragService = ragService;
    }

    @PostMapping("/index")
    public Map<String, Object> indexDocuments(@RequestBody Map<String,Object> request) {
        String directoryPath = (String) request.getOrDefault(
                "directory", "src/main/resources/data/wiki"
        );
        return ragService.indexDocuments(directoryPath);
    }

    @PostMapping("/search")
    public Map<String, Object> search(@RequestBody Map<String,Object> request) {
        String query = (String) request.get("query");
        int topK = request.containsKey("toy_k")
                ? ((Number) request.get("toy_k")).intValue()
                : 5;
        return Map.of(
                "results", ragService.search(query, topK)
        );
    }

    @PostMapping("/update")
    public Map<String, Object> updateDocuments(@RequestBody Map<String,Object> request) {
        String directoryPath = (String) request.getOrDefault(
                "directory", "src/main/resources/data/wiki"
        );
        return ragService.updateDocuments(directoryPath);
    }
}
