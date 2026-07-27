package com.minecraft.agent.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import dev.langchain4j.store.embedding.chroma.ChromaEmbeddingStore;
import org.springframework.context.annotation.Bean;

/**
 * @program: agentWithMinecraft
 * @description: ChromaDB 连接配置
 * @author: pokerjiyin
 * @create: 2026-07-26 22:56
 **/

@Data
@Configuration
@ConfigurationProperties(prefix = "chromadb")
public class ChromaConfig {
    private String host;
    private int port;

    public String getBeanUrl(){
        return String.format("http://%s:%d", host, port);
    }
}
