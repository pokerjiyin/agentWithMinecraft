/**
 * websocket.js — WebSocket 实时通信
 * 路径：/ws/bot
 * 实时推送 Bot 状态变化给前端/Java
 */
const WebSocket = require("ws");

module.exports = function(server, botRef){
  const wss = new WebSocket.Server({server, path: "/ws/bot"});

  // 心跳间隔
  const PUSH_INTERVAL = 1000; // 每秒推送一次状态

  wss.on("connection", (ws) => {
    console.log("[WS] 客户端已连接");

    // 定时推送 Bot 状态
    const interval = setInterval(() => {
      if(ws.readyState === WebSocket.OPEN){
        const state = botRef.getState();
        ws.send(
          JSON.stringify({
            type: "status",
            data: state,
            timestamp: Date.now(),
          })
        );
      }
    }, PUSH_INTERVAL);

    ws.on("close", () => {
      console.log("[WS] 客户端已断开");
      clearInterval(interval);
    });

    ws.on("error", (err) => {
      console.error(`[WS] 错误: ${err.message}`);
      clearInterval(interval);
    });
  });

  return wss;
};