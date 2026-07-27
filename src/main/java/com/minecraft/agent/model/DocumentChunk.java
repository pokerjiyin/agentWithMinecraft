package com.minecraft.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * @program: agentWithMinecraft
 * @description: 为数据切分后的数据定一个格式存入向量库
 * @author: pokerjiyin
 * @create: 2026-07-27 21:51
 **/

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentChunk {
    private String id;
    private String type;         // 合成配方recipe / 教程tutorial / 游戏机制mechanics
    private String title;
    private String content;
    private String source;
    private List<String> tags;
    private Map<String,Object> metadata;
    private String md5Hash;
}
