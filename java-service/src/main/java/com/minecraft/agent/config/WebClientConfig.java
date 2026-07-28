package com.minecraft.agent.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * @program: agentWithMinecraft
 * @description: Http客户端配置
 * @author: pokerjiyin
 * @create: 2026-07-27 21:02
 **/

@Configuration
public class WebClientConfig {

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder();
    }
}
