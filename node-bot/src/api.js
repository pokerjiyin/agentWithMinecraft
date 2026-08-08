/**
 * api.js — Express HTTP API
 * 将 Java 转发来的指令路由到对应的 handler
 */
const express = require("express")
const router = express.Router()
const{
  handleMove,
  handleDig,
  handleChopTree,
  handleCraft,
  handleUse,
  handleOpenChest,
} = require("./handlers")

module.exports = function(botRef){
  // botRef 是一个 { getBot } 对象，每次请求动态获取最新 bot 实例
  // botRef = {getBot, getState, createBot, disconnect, setTaskActive}
  // ===== 辅助：任务包装器（标记任务开始/结束） =====
  function withTask(fn) {
    return async (req, res) => {
      botRef.setTaskActive(true);
      try {
        await fn(req, res);
      } finally {
        botRef.setTaskActive(false);
      }
    };
  }

  // ===== 辅助：获取在线 bot =====
  function requireBot(){
    const bot = botRef.getBot();
    if(!bot){
      const err = new Error("Bot 未连接")
      err.statusCode = 503;
      throw err;
    }
    if (!botRef.getState().online) {
      const err = new Error("Bot 未进入游戏，请先启动 Minecraft 服务器");
      err.statusCode = 503;
      throw err;
    }
    return bot;
  }

  // ===== 移动 =====
  router.post("/api/bot/move", withTask(async(req, res) => {
    try{
      const bot = requireBot();
      const{x, y, z} = req.body;
      const result = await handleMove(bot, x, y, z);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({error: e.message});
    }
  }));

  // ===== 挖掘 =====
  router.post("/api/bot/dig", withTask(async(req, res) => {
    try{
      const bot = requireBot();
      const{x, y, z} = req.body;
      const result = await handleDig(bot, x, y, z);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  }));
  
  // ===== 砍树 =====
  router.post("/api/bot/chop_tree", withTask(async(req, res) => {
    try{
      const bot = requireBot();
      const{x, y, z} = req.body;
      const result = await handleChopTree(bot, x, y, z);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  }));

  // ===== 合成 =====
  router.post("/api/bot/craft", withTask(async(req, res) => {
    try{
      const bot = requireBot();
      const{itemName, count} = req.body;
      const result = await handleCraft(bot, itemName, count || 1);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  }));

  // ===== 使用物品 =====
  router.post("/api/bot/use", withTask(async(req, res) => {
    try {
      const bot = requireBot();
      const { action, target, itemName } = req.body;
      const result = await handleUse(bot, action, target || null, itemName || null);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  }));

  // ===== 打开箱子 =====
  router.post("/api/bot/open_chest", withTask(async(req, res) => {
    try{
      const bot = requireBot();
      const{x, y ,z} = req.body;
      const result = await handleOpenChest(bot, x, y, z);
      res.json(result);
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  }));

  // ===== 状态查询 =====
  router.get("/api/bot/status", (req, res) => {
    res.json(botRef.getState());
  });
  
  // ===== 背包查询 =====
  router.get("/api/bot/inventory", (req, res) => {
    const state = botRef.getState();
    res.json({inventory: state.inventory, heldItem: state.heldItem});
  });

  // ===== 连接服务器 =====
  router.post("/api/bot/connect", (req, res) => {
    try {
      const bot = botRef.getBot();
      if (bot) {
        return res.json({ success: true, message: "已经连接" });
      }
      botRef.createBot();
      res.json({ success: true, message: "正在连接..." });
    }catch(e){
      res.status(500).json({ error: e.message });
    }
  });

  // ===== 断开连接 =====
  router.post("/api/bot/disconnect", (req, res) => {
    botRef.disconnect();
    res.json({ success: true, message: "已断开" });
  });

  // ===== 聊天 =====
  router.post("/api/bot/chat", (req, res) => {
    try{
      const bot = requireBot();
      const{message} = req.body;
      bot.chat(message);
      res.json({success: true, message})
    }catch(e){
      res.status(e.statusCode || 500).json({ error: e.message });
    }
  });

  // ===== 健康检查 =====
  router.get("/health", (req, res) => {
    res.json({ service: "minecraft-bot-node", status: "UP" });
  });

  return router;
};