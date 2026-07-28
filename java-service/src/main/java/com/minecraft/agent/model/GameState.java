package com.minecraft.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * @program: agentWithMinecraft
 * @description: 游戏中状态
 * @author: pokerjiyin
 * @create: 2026-07-27 22:04
 **/

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GameState {
    //位置
    private double x;
    private double y;
    private double z;

    //生命值
    private double health;          /*当前生命值*/
    private double maxHealth;       /*最大生命值*/

    //饥饿值
    private int food;
    private double saturation;      /*额外的饥饿值（游戏中饥饿值的金色外轮廓）*/

    //背包
    private List<Map<String,Object>> inventory;

    //手持物品
    private Map<String,Object> heldItem;

    //游戏模式
    private String gameMode;

    //是否在线
    private boolean online;
}
