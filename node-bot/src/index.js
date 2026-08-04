/**
 * index.js — Minecraft AI Bot 入口
 * 启动 Express + WebSocket + Mineflayer Bot
 */
const express = require("express");
const http = require("http");
const path = require("path");
require("dotenv").config({path: path.resolve(__dirname, "../../.env")});

const{createBot, getBot, getState, disconnect} = require("./bot");
const createApiRouter = require("./api");
const createWebSocket = require("./websocket");

// ===== 创建 Express 和 HTTP Server =====
const app = express();
app.use(express.json());

const server = http.createServer(app);

// ===== Bot 引用（传给 api 和 websocket） =====
const botRef = {getBot, getState, createBot, disconnect};

// ===== 挂载 API 路由 =====
app.use(createApiRouter(botRef));

// ===== 挂载 WebSocket =====
createWebSocket(server, botRef);

// ===== 启动 =====
const PORT = process.env.NODE_PORT || 3000;

server.listen(PORT, () => {
  console.log(`[Server] HTTP + WS 已启动 → http://localhost:${PORT}`);
  console.log(`[Server] WebSocket → ws://localhost:${PORT}/ws/bot`);

  // 自动连接 Minecraft
  console.log("[Bot] 正在连接 Minecraft...");
  createBot();
});