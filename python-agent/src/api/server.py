"""
FastAPI 服务 —— Agent 对外 HTTP API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from ..agent.graph import build_graph
from ..agent.state import AgentState
from ..memory.checkpoint import get_checkpointer


# ===== 请求 / 响应模型 =====
class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    intent: str


# ===== FastAPI（lifespan 中编译 Agent） =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时创建 checkpointer 并编译 Agent"""
    checkpointer = await get_checkpointer()
    app.state.agent = build_graph().compile(checkpointer=checkpointer)
    yield


app = FastAPI(
    title="Minecraft AI Agent",
    description="基于 LangGraph 的 Minecraft 游戏智能体 API",
    version="0.1.0",
    lifespan=lifespan,
)


# ===== 路由 =====
@app.get("/health")
async def health():
    """健康检查"""
    return {
        "service": "minecraft-agent-python",
        "status": "UP",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    """接收用户消息，返回 Agent 响应"""
    try:
        config = {"configurable": {"thread_id": req.thread_id}}

        initial_state: AgentState = {
            "messages": [HumanMessage(content=req.message)],
            "intent": "",
            "plan": [],
            "current_step": 0,
            "rag_context": "",
            "game_state": "{}",
            "task_completed": False,
        }

        result = await request.app.state.agent.ainvoke(initial_state, config)

        # 提取最后一条 AI 消息
        messages = result.get("messages", [])
        reply = ""
        for msg in reversed(messages):
            if msg.type == "ai":
                reply = msg.content
                break

        if not reply:
            reply = "（Agent 处理完成，请查看上一条回复）"

        return ChatResponse(
            thread_id=req.thread_id,
            reply=reply,
            intent=result.get("intent", "unknown"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def agent_status():
    """返回 Agent 当前状态"""
    return {
        "service": "minecraft-agent-python",
        "status": "idle",
    }


@app.post("/cancel")
async def cancel_task():
    """取消当前任务（TODO: 阶段四实现）"""
    return {"status": "ok", "message": "任务取消功能将在阶段四实现"}


@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """获取指定会话的对话历史（TODO: 阶段四实现）"""
    return {
        "thread_id": thread_id,
        "messages": [],
        "note": "对话历史查询将在阶段四实现",
    }
