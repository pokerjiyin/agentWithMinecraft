package com.minecraft.agent.service;

import org.springframework.context.annotation.Lazy;
import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.DocumentSplitter;
import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.parser.TextDocumentParser;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiEmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.EmbeddingSearchResult;
import dev.langchain4j.store.embedding.chroma.ChromaEmbeddingStore;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.security.MessageDigest;
import java.util.*;

/**
 * @program: java-service
 * @description:
 * @author: pokerjiyin
 * @create: 2026-08-04 13:31
 **/

@Lazy
@Slf4j
@Service
public class RagService {

    private final EmbeddingModel embeddingModel;
    private final String collectionName;
    private final org.springframework.web.reactive.function.client.WebClient chromaClient;
    private EmbeddingStore<TextSegment> embeddingStore;

    @Value("${rag.chunk-size:500}")
    private int chunkSize;

    @Value("${rag.chunk-overlap:50}")
    private int chunkOverlap;

    @Value("${rag.top-k:5}")
    private int topK;

    public RagService(
            @Value("${dashscope.api-key}") String apiKey,
            @Value("${dashscope.base-url}") String baseUrl,
            @Value("${dashscope.embedding-model}") String embeddingModelName,
            @Value("${chromadb.host}") String chromaHost,
            @Value("${chromadb.port}") int chromaPort,
            @Value("${rag.collection-prefix:minecraft}") String collectionPrefix
    ){

        // Embedding 模型（DeepSeek，兼容 OpenAI API）
        this.embeddingModel = OpenAiEmbeddingModel.builder()
                .apiKey(apiKey)
                .baseUrl(baseUrl)
                .modelName(embeddingModelName)
                .build();

        this.collectionName = collectionPrefix + "_wiki";
        this.chromaClient = org.springframework.web.reactive.function.client.WebClient.builder()
                .baseUrl("http://" + chromaHost + ":" + chromaPort)
                .build();

        // TODO: ChromaDB 部署后取消注释
        // ChromaDB 未部署，暂时跳过连接
        this.embeddingStore = null;
        log.info("RagService 初始化完成（ChromaDB 暂未连接）");
    }

    // ===== 文档索引 =====
    /**
     * 批量索引文档目录下的所有 txt/md 文件
     */
    public Map<String, Object> indexDocuments(String directoryPath){

        if (embeddingStore == null) {
            return Map.of("status", "error", "message", "ChromaDB 未连接");
        }

        File dir = new File(directoryPath);
        if(!dir.exists() || !dir.isDirectory()){
            throw new RuntimeException("目录不存在: " + directoryPath);
        }

        File[] files = dir.listFiles(
                (d, name) -> name.endsWith(".txt") || name.endsWith(".md")
        );
        if(files == null || files.length == 0){
            return Map.of("status", "ok", "message", "没有可索引的文件");
        }

        int totalChunks = 0;
        for(File file : files){

            if (getStoredHash(file.getName()) != null) {
                log.debug("文件已存在，跳过: {}", file.getName());
                continue;
            }

            List<TextSegment> chunks = loadAndSplit(file);
            List<Embedding> embeddings = embeddingModel.embedAll(chunks).content();
            embeddingStore.addAll(embeddings, chunks);
            totalChunks += chunks.size();
            log.info("已索引: {} → {} 个片段", file.getName(), chunks.size());

            //索引成功后必须记录 MD5，否则下次还会再索引一遍
            saveHash(file.getName(), md5(file));
        }

        return Map.of(
                "status", "ok",
                "files", files.length,
                "chunks", totalChunks
        );
    }

    // ===== 向量检索 =====
    /**
     * Top-K 相似度检索
     */
    public List<Map<String, Object>> search(String query, int k){

        if (embeddingStore == null) {
            log.warn("RAG 检索失败：ChromaDB 未连接");
            return List.of();
        }

        Embedding queryEmbedding = embeddingModel.embed(query).content();

        EmbeddingSearchRequest request = EmbeddingSearchRequest.builder()
                .queryEmbedding(queryEmbedding)
                .maxResults(k)
                .build();

        EmbeddingSearchResult<TextSegment> result = embeddingStore.search(request);

        return result.matches().stream().map(match -> {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("score", Math.round(match.score() * 10000.0) / 10000.0);
            item.put("content", match.embedded().text());
            item.put("metadata", match.embedded().metadata().toMap());
            return item;
        }).toList();
    }

    // ===== MD5 更新 =====
    public Map<String, Object> updateDocuments(String directoryPath){

        if (embeddingStore == null) {
            return Map.of("status", "error", "message", "ChromaDB 未连接");
        }

        File dir = new File(directoryPath);
        if(!dir.exists() || !dir.isDirectory()){
            throw new RuntimeException("目录不存在: " + directoryPath);
        }

        File[] files = dir.listFiles(
                (d, name) -> name.endsWith(".txt") || name.endsWith(".md")
        );
        if(files == null){
            return Map.of("status", "ok", "message", "没有文件");
        }

        int updated = 0;
        int skipped = 0;
        for(File file : files){
            String newHash = md5(file);
            String oldHash = getStoredHash(file.getName());

            if(newHash.equals(oldHash)){
                skipped++;
                log.debug("未变更，跳过: {}", file.getName());
            }else{
                // 删除旧向量
                Map<String, Object> where = Map.of("source", file.getName());
                chromaClient.post()
                        .uri("/api/v2/tenant/default_tenant/database/default_database/collections/"
                                + collectionName + "/delete")
                        .bodyValue(Map.of("where", where))
                        .retrieve()
                        .toBodilessEntity()
                        .block();

                // 重新索引
                List<TextSegment> chunks = loadAndSplit(file);
                List<Embedding> embeddings = embeddingModel.embedAll(chunks).content();
                embeddingStore.addAll(embeddings, chunks);

                // 更新 hash
                saveHash(file.getName(), newHash);
                updated++;
                log.info("已更新: {}", file.getName());
            }
        }

        return Map.of(
                "status", "ok",
                "updated", updated,
                "skipped", skipped
        );
    }

    // ===== 私有方法 =====
    private List<TextSegment> loadAndSplit(File file){
        Document document = FileSystemDocumentLoader.loadDocument(
                file.toPath(),
                new TextDocumentParser()
        );

        DocumentSplitter splitter = DocumentSplitters.recursive(
                chunkSize, chunkOverlap
        );

        List<TextSegment> segments = splitter.split(document);

        // 给每个片段标记来源文件，用于后续精确删除
        return segments.stream()
                .map(seg -> TextSegment.from(
                        seg.text(),
                        Metadata.from("source", file.getName())
                ))
                .toList();
    }

    private String md5(File file){
        try{
            MessageDigest md =MessageDigest.getInstance("MD5");
            byte[] bytes = java.nio.file.Files.readAllBytes(file.toPath());
            byte[] digest = md.digest(bytes);
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        }catch(Exception e){
            throw new RuntimeException("MD5 计算失败: " + file.getName(), e);
        }
    }

    // TODO: 以下两个方法在生产中应持久化到文件/数据库，现阶段用内存 Map
    private final Map<String, String> hashStore = new HashMap<>();

    private String getStoredHash(String fileName){
        return hashStore.get(fileName);
    }

    private void saveHash(String fileName, String hash){
        hashStore.put(fileName, hash);
    }

}
