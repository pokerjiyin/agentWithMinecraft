/**
 * handlers.js — 游戏操控处理器
 * 每个函数实现一个具体的游戏操作
 */

const {Vec3} = require("vec3");
const {Movements, goals} = require("mineflayer-pathfinder");

// ===== 移动 =====
/**
 * 移动到目标坐标（使用 pathfinder 自动寻路）
 * 自动绕障碍、跳台阶，无需手动按键
 * @param {Bot} bot - Mineflayer Bot 实例
 * @param {number} x
 * @param {number} y
 * @param {number} z
 * @returns {Promise<{success: boolean, position: object}>}
 */
async function handleMove(bot, x, y, z){
  const target = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));

  // 配置寻路参数
  const movements = new Movements(bot);
  movements.canDig = false;       // 不自动挖方块（避免误挖）
  movements.canPlace = false;     // 不自动放置方块
  bot.pathfinder.setMovements(movements);

  // 设置目标（GoalBlock 让 bot 走到方块旁）
  const goal = new goals.GoalBlock(target.x, target.y, target.z);
  bot.pathfinder.setGoal(goal);

  // 等待到达（轮询位置）
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      clearInterval(check);
      reject(new Error("移动超时"));
    }, 30000);

    const check = setInterval(() => {
      const pos = bot.entity.position;
      const dist = pos.distanceTo(target);
      if (dist < 2) {
        clearInterval(check);
        clearTimeout(timeout);
        bot.pathfinder.setGoal(null);  // 清除目标，停止移动
        resolve();
      }
    }, 200);
  });

  return {
    success: true,
    position: {
      x: bot.entity.position.x,
      y: bot.entity.position.y,
      z: bot.entity.position.z,
    },
  };
}

// ===== 挖掘 =====
/**
 * 挖掘指定坐标的方块
 * @param {Bot} bot
 * @param {number} x
 * @param {number} y
 * @param {number} z
 * @returns {Promise<{success: boolean, block: object}>}
 */
async function handleDig(bot, x, y ,z){
  const target = new Vec3(x, y, z);
  const block = bot.blockAt(target);

  if(!block || block.name === "air"){
    throw new Error(`坐标 (${x}, ${y}, ${z}) 没有可挖掘的方块`);
  }

  // 确保能到达
  await bot.lookAt(target);
  await bot.tool.equipForBlock(block);

  // 如果距离太远，先走近
  const dist = bot.entity.position.distanceTo(target);
  if(dist > 4.5){
    await handleMove(bot, x, y + 1, z);
  }

  await bot.dig(block);

  return {
    success: true,
    block: {name: block.name, x, y, z},
  }
}

// ===== 砍树 =====
/**
 * 砍树：从底部开始逐块破坏树干
 * @param {Bot} bot
 * @param {number} x - 树干底部 x
 * @param {number} y - 树干底部 y
 * @param {number} z - 树干底部 z
 * @returns {Promise<{success: boolean, logsBroken: number}>}
 */
async function handleChopTree(bot, x, y, z){
  const woodTypes = ["oak_log", "birch_log", "spruce_log", "jungle_log",
                       "acacia_log", "dark_oak_log", "mangrove_log",
                       "cherry_log", "crimson_stem", "warped_stem"];

  let logsBroken = 0;

  // 砍树前，先走近
  const treeBase = new Vec3(x, y, z);
  const dist = bot.entity.position.distanceTo(treeBase);
  if (dist > 4.5) {
    await handleMove(bot, x, y + 1, z);
  }

  for(let cy = y; cy < y + 30; cy ++){
    const block = bot.blockAt(new Vec3(x, cy, z));
    if(!block || !woodTypes.includes(block.name))
      break;

    await bot.lookAt(block.position);
    await bot.tool.equipForBlock(block);
    await bot.dig(block);
    logsBroken++;
  }
  
  return {success: true, logsBroken};
}

// ===== 合成 =====
/**
 * 合成物品
 * @param {Bot} bot
 * @param {string} itemName - 物品名称，如 "stone_pickaxe"
 * @param {number} count - 数量
 * @returns {Promise<{success: boolean, crafted: object}>}
 */
async function handleCraft(bot, itemName, count = 1){
  const recipe = bot.recipesFor(require("minecraft-data")(bot.version).itemsByName[itemName]?.id);

  if(!recipe || recipe.length === 0){
    throw new Error(`未找到配方: ${itemName}`);
  }

  await bot.craft(recipe[0], count, null);
  return {
    success: true,
    crafted: {
      name: itemName,
      count,
    }
  };
}

// ===== 使用物品 =====
/**
 * 使用物品（吃食物 / 放置方块 / 右键交互）
 * @param {Bot} bot
 * @param {string} action - "eat" | "place" | "interact"
 * @param {object} target - { x, y, z } 用于 place/interact
 * @returns {Promise<{success: boolean}>}
 */
async function handleUse(bot, action, target = null ,itemName = null){
  if(action === "eat"){
    const food = bot.inventory.items().find(
      (item) => item.foodPoints > 0
    );
    if(!food) throw new Error("背包中没有食物");
    await bot.equip(food, "hand");
    await bot.consume();
    return {
      success: true,
      action: "eat"
    };
  }

  if(action === "place" && target){
    if (!itemName) throw new Error("place 操作需要指定物品名称");
    const block = bot.blockAt(new Vec3(target.x , target.y, target.z));
    if (!block || block.name === "air") {
      throw new Error(`无法放置：(${target.x}, ${target.y}, ${target.z}) 是空气`);
    }
    // 从背包里找名字匹配的物品
    const item = bot.inventory.items().find((i) => i.name === itemName);

    if (!item) throw new Error(`背包中没有 ${itemName}`);
    await bot.equip(item, "hand");
    await bot.placeBlock(block, new Vec3(0, 1, 0));
    return { success: true, action: "place" };
  }

  if (action === "interact" && target){
    const block = bot.blockAt(new Vec3(target.x, target.y, target.z));
    if (!block || block.name === "air") {
      throw new Error(`无法交互：(${target.x}, ${target.y}, ${target.z}) 是空气`);
    }
    try {
      await bot.activateBlock(block);
      return { success: true, action: "interact" };
    } catch (e) {
      throw new Error(`交互失败：方块 ${block.name} 不支持右键操作`);
    }
  }

  throw new Error(`未知操作: ${action}`);
}

// ===== 打开箱子 =====
/**
 * 打开箱子并查看内容
 * @param {Bot} bot
 * @param {number} x
 * @param {number} y
 * @param {number} z
 * @returns {Promise<{success: boolean, items: Array}>}
 */
async function handleOpenChest(bot, x, y, z){
  const chest = bot.blockAt(new Vec3(x, y, z));

  if (!chest || !chest.name.includes("chest")){
    throw new Error(`坐标 (${x}, ${y}, ${z}) 不是箱子`);
  }

  const window = await bot.openContainer(chest);
  const items = window.containerItems().map((item) => ({
    name: item.name,
    count: item.count,
    slot: item.slot,
  }));

  await window.close();
  return { success: true, items };
}

module.exports = {
  handleMove,
  handleDig,
  handleChopTree,
  handleCraft,
  handleUse,
  handleOpenChest,
};