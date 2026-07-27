package com.minecraft.agent.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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

    @PostMapping("/index")
    public Map<String,Object> indexDocuments(@RequestBody Map<String,Object> request) {
        return Map.of("status", "ok", "message", "RAG index - to be implemented");
    }

    @PostMapping("/search")
    public Map<String,Object> search(@RequestBody Map<String,Object> request) {
        return Map.of("status", "ok", "message", "RAG search - to be implemented");
    }

    @PostMapping("/update")
    public Map<String,Object> updateDocuments(@RequestBody Map<String,Object> request) {
        return Map.of("status", "ok", "message", "RAG update - to be implemented");
    }
}
