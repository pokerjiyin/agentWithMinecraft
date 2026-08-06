package com.minecraft.agent.controller;

import com.minecraft.agent.service.ToolForwardService;
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

    private final ToolForwardService toolService;

    public ToolController(ToolForwardService toolService) {
        this.toolService = toolService;
    }

    @PostMapping("/move")
    public Map<String, Object> move(@RequestBody Map<String,Object> req) {
        double x = ((Number) req.get("x")).doubleValue();
        double y = ((Number) req.get("y")).doubleValue();
        double z = ((Number) req.get("z")).doubleValue();
        return toolService.move(x, y, z);
    }

    @PostMapping("/dig")
    public Map<String,Object> dig(@RequestBody Map<String,Object> req) {
        int x = ((Number) req.get("x")).intValue();
        int y = ((Number) req.get("y")).intValue();
        int z = ((Number) req.get("z")).intValue();
        return toolService.chopTree(x, y, z);
    }

    @PostMapping("/chop_tree")
    public Map<String, Object> chopTree(@RequestBody Map<String, Object> req) {
        int x = ((Number) req.get("x")).intValue();
        int y = ((Number) req.get("y")).intValue();
        int z = ((Number) req.get("z")).intValue();
        return toolService.chopTree(x, y, z);
    }

    @PostMapping("/craft")
    public Map<String, Object> craft(@RequestBody Map<String, Object> req) {
        String recipe = (String) req.get("recipe");
        int count = req.containsKey("count")
                ? ((Number) req.get("count")).intValue()
                : 1;
        return toolService.craft(recipe, count);
    }

    @PostMapping("/use")
    public Map<String, Object> useItem(@RequestBody Map<String, Object> req) {
        String action = (String) req.get("action");
        Object targetObj = req.get("target");
        Map<String, Object> target = null;
        if (targetObj instanceof Map){
            @SuppressWarnings("unchecked")
            Map<String, Object> t = (Map<String, Object>) targetObj;
            target = t;
        }
        String itemName = (String) req.get("itemName");
        return toolService.use(action, target, itemName);
    }

    @PostMapping("/open_chest")
    public Map<String, Object> openChest(@RequestBody Map<String, Object> req) {
        int x = ((Number) req.get("x")).intValue();
        int y = ((Number) req.get("y")).intValue();
        int z = ((Number) req.get("z")).intValue();
        return toolService.openChest(x, y, z);
    }

    @GetMapping("/status")
    public Map<String, Object> getStatus() {
        return toolService.getStatus();
    }

    @GetMapping("/inventory")
    public Map<String, Object> getInventory() {
        return toolService.getInventory();
    }

    @PostMapping("/chat")
    public Map<String, Object> chat(@RequestBody Map<String, Object> req) {
        String message = (String) req.get("message");
        return toolService.chat(message);
    }
}
