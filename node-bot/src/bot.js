/**
 * bot.js — Mineflayer Bot 封装
 * 连接管理、状态追踪、断连重连、卡死检测
 */
const mineflayer = require("mineflayer");
const path = require("path");
const pathfinder = require("mineflayer-pathfinder").pathfinder;
require("dotenv").config({path: path.resolve(__dirname,"../../.env")});

// ===== 配置 =====
const CONFIG = {
  host: process.env.MINECRAFT_HOST || "localhost",
  port: parseInt(process.env.MINECRAFT_PORT || "25565"),
  username: process.env.MINECRAFT_USERNAME || "AI_Bot",
  auth: process.env.MINECRAFT_AUTH || "offline",
};

// ===== 重连配置 ===== 
const RECONNECT = {
  enabled: true,
  initialDelay: 1000, // 1 秒
  maxDelay: 30000, // 30 秒
  multiplier: 2,
};

// ===== 卡死检测配置 =====
const STUCK = {
  checkInterval: 10000, // 每 10 秒检查
  thresholdMs: 120000, // 120 秒不移动视为卡死
};

// ===== Bot 实例与状态 =====
let bot = null;
let reconnectAttempts = 0;
let reconnectTimer = null;
let stuckTimer = null;

let lastPosition = null;
let lastMoveTime = Date.now();
let taskActive = false; // 当前是否在执行任务

// 实时状态
const state = {
  online: false,
  x: 0,
  y: 0,
  z: 0,
  health: 0,
  maxHealth: 20,
  food: 0,
  saturation: 0,
  gameMode: "survival",
  inventory: [],
  heldItem: null,
};

// ===== 核心方法 =====
function createBot(){
  bot = mineflayer.createBot({
    host: CONFIG.host,
    port: CONFIG.port,
    username: CONFIG.username,
    auth: CONFIG.auth,
    hideErrors: false,
  });

  bot.loadPlugin(pathfinder);
  registerEvents(bot);
  return bot;
}

function getBot(){
  return bot;
}

function getState(){
  // 更新背包数据（实时读取）
  if(bot && bot.inventory){
    state.inventory = bot.inventory.items().map((item) => ({
      name: item.name,
      count: item.count,
      slot: item.slot,
    }));
    state.heldItem = bot.heldItem ? {name: bot.heldItem.name, count: bot.heldItem.count} : null;
  }
  return { ...state };
}

// ===== 事件注册 =====
function registerEvents(bot){
  bot.once("spawn", onSpawn);
  bot.on("end", onEnd);
  bot.on("error", onError);
  bot.on("kicked", onKicked);
  bot.on("death", onDeath);
  bot.on("health", onHealth);
  bot.on("move", onMove);
}

function onSpawn(){
  console.log(`[Bot]已加入服务器 -> ${CONFIG.host}:${CONFIG.port}`);
  state.online = true;
  reconnectAttempts = 0;
  lastMoveTime = Date.now();
  startStuckDetection();
}

function onEnd(reason){
  console.log(`[Bot] 连接断开: ${reason}`)
  state.online = false;
  clearStuckDetection();
  scheduleReconnect();
}

function onError(err){
  console.error(`[Bot] 错误: ${err.message}`);
}

function onKicked(reason){
  const msg = JSON.parse(reason).text || reason;
  console.log(`[Bot] 被踢出: ${msg}`);
  state.online = false;
  clearStuckDetection();
  scheduleReconnect();
}

function onDeath(){
  console.log("[Bot] 角色死亡，等待重生...");
}

function onHealth(){
  state.health = bot.health;
  state.food = bot.food;
  state.saturation = bot.foodSaturation || 0;
}

function onMove(){
  if(bot && bot.entity){
    const pos = bot.entity.position;
    state.x = Math.round(pos.x * 10) / 10;
    state.y = Math.round(pos.y * 10) / 10;
    state.z = Math.round(pos.z * 10) / 10;
  }

  // 检测是否真的移动了
  if(
    lastPosition && 
    lastPosition.x === state.x && 
    lastPosition.y === state.y && 
    lastPosition.z === state.z
  ){
    return; // 视角转动不算移动
  }
  lastPosition = {x: state.x, y: state.y, z: state.z};
  lastMoveTime = Date.now();
}

// ===== 断连重连（指数退避） =====
function scheduleReconnect(){
  if(!RECONNECT.enabled) return;

  const delay = Math.min(
    RECONNECT.initialDelay * Math.pow(RECONNECT.multiplier, reconnectAttempts),
    RECONNECT.maxDelay
  );
  reconnectAttempts++;

  console.log(`[Bot] ${delay / 1000}s 后尝试第 ${reconnectAttempts} 次重连...`)

  reconnectTimer = setTimeout(() => {
    console.log("[Bot] 正在重连...");
    createBot();
  }, delay);
}

function cancelReconnect(){
  if(reconnectTimer){
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

// ===== 卡死检测 =====
function startStuckDetection(){
  stuckTimer = setInterval(() => {
    if (!state.online) return;
    if (!taskActive) return;  // ← 空闲时跳过检测
    const idle = Date.now() - lastMoveTime;
    if (idle > STUCK.thresholdMs) {
      console.log(`[Bot] 卡死检测：${idle / 1000}s 未移动，强制重连`);
      state.online = false;
      clearStuckDetection();
      bot.end("卡死重连");
    }
  }, STUCK.checkInterval);
}

function clearStuckDetection() {
  if (stuckTimer) {
    clearInterval(stuckTimer);
    stuckTimer = null;
  }
}

// ===== 主动断开 =====
function disconnect(){
  RECONNECT.enabled = false;
  cancelReconnect();
  clearStuckDetection();
  if (bot) {
    bot.end("主动断开");
    bot = null;
  }
  state.online = false;
  RECONNECT.enabled = true;
}

module.exports = {
  createBot,
  getBot,
  getState,
  disconnect,
  setTaskActive: (active) => { taskActive = active; },
};