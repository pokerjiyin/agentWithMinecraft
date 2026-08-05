package com.minecraft.agent.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

/**
 * @program: java-service
 * @description:
 * @author: pokerjiyin
 * @create: 2026-08-05 16:48
 **/

@Slf4j
@Service
public class ToolForwardService {

    private final WebClient webClient;

    public ToolForwardService(
            @Value("${nodejs.service-url}") String nodeServiceUrl){
        this.webClient = WebClient.builder()
                .baseUrl(nodeServiceUrl)
                .build();
        log.info("ToolForwardService 初始化完成 → {}", nodeServiceUrl);
    }

    // ===== 移动 =====
    public Map<String, Object> move(double x, double y, double z){
        return post("/api/bot/move", Map.of("x", x, "y", y, "z", z));
    }

    // ===== 挖掘 =====
    public Map<String, Object> dig(int x, int y, int z) {
        return post("/api/bot/dig", Map.of("x", x, "y", y, "z", z));
    }

    // ===== 砍树 =====
    public Map<String, Object> chopTree(int x, int y, int z) {
        return post("/api/bot/chop_tree", Map.of("x", x, "y", y, "z", z));
    }

    // ===== 合成 =====
    public Map<String, Object> craft(String recipeName, int count) {
        return post("/api/bot/craft", Map.of("itemName", recipeName, "count", count));
    }

    // ===== 使用物品 =====
    public Map<String, Object> use(String action, Map<String, Object> target, String itemName) {
        Map<String, Object> body = new java.util.LinkedHashMap<>();
        body.put("action", action);
        if (target != null) body.put("target", target);
        if (itemName != null) body.put("itemName", itemName);
        return post("/api/bot/use", body);
    }

    // ===== 打开箱子 =====
    public Map<String, Object> openChest(int x, int y, int z) {
        return post("/api/bot/open_chest", Map.of("x", x, "y", y, "z", z));
    }

    // ===== 状态查询 =====
    public Map<String, Object> getStatus() {
        return get("/api/bot/status");
    }

    // ===== 背包查询 =====
    public Map<String, Object> getInventory() {
        return get("/api/bot/inventory");
    }

    // ===== 聊天 =====
    public Map<String, Object> chat(String message) {
        return post("/api/bot/chat", Map.of("message", message));
    }

    // ===== 通用 HTTP 方法 =====
    @SuppressWarnings("unchecked")
    private Map<String, Object> post(String path, Object body) {
        try {
            return webClient.post()
                    .uri(path)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (Exception e) {
            log.error("POST {} 失败: {}", path, e.getMessage());
            return Map.of("success", false, "error", e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> get(String path) {
        try {
            return webClient.get()
                    .uri(path)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (Exception e) {
            log.error("GET {} 失败: {}", path, e.getMessage());
            return Map.of("success", false, "error", e.getMessage());
        }
    }

}
