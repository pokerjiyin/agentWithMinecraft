package com.minecraft.agent.controller;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * @program: agentWithMinecraft
 * @description: 工具转发占位
 * @author: pokerjiyin
 * @create: 2026-07-27 22:44
 **/

@RestController
@RequestMapping("/api/tools")
public class ToolController {

    @PostMapping("/move")
    public Map<String,Object> move(@RequestBody Map<String,Object> request) {
        return Map.of("status","ok","message","Move - to be implemented");
    }

    @PostMapping("/dig")
    public Map<String,Object> dig(@RequestBody Map<String,Object> request) {
        return Map.of("status","ok","message","Dig - to be implemented");
    }

    @GetMapping("/status")
    public Map<String,Object> getStatus() {
        return Map.of("status","ok","message","Status - to be implemented");
    }
}
