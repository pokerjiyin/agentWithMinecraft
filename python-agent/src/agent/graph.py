"""
LangGraph StateGraph 构建
定义节点 + 条件边 = 完整的 Agent 决策流
"""
import json

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    analyze_intent,
    chat_reply,
    rag_retrieve,
    agent,
    execute_tool
)


def build_graph():
    """
    构建 ReAct 循环状态机

    analyze_intent
     ├─ "chat" → chat_reply → END
     └─ "game" → rag_retrieve → agent ──→ execute_tool ──┐
                            ↑                            │
                            └───────观察结果───────────────┘
                            │
                        判断：answer？→ END
    """
    workflow = StateGraph(AgentState)

    # ===== 添加节点 =====
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("chat_reply", chat_reply)
    workflow.add_node("rag_retrieve", rag_retrieve)
    workflow.add_node("agent", agent)
    workflow.add_node("execute_tool", execute_tool)

    # ===== 入口 =====
    workflow.set_entry_point("analyze_intent")

    # ===== 条件边：意图路由 =====
    def route_intent(state: AgentState) -> str:
        intent = state.get("intent","chat")
        return "chat" if intent == "chat" else "game"

    workflow.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {
            "chat": "chat_reply",
            "game": "rag_retrieve",
        }
    )

    # ===== 闲聊结束 =====
    workflow.add_edge("chat_reply",END)

    # ===== 游戏指令线性流程 =====
    workflow.add_edge("rag_retrieve","agent")

    # ===== ReAct 循环：agent → 调工具 或 结束 =====
    def route_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        try:
            data = json.loads(last.content)
            return "execute_tool" if "tool" in data else "end"
        except (json.JSONDecodeError, TypeError):
            return "end"

    workflow.add_conditional_edges(
        "agent",
        route_agent,
        {"execute_tool": "execute_tool", "end": END},
    )

    # ===== ReAct 循环：执行完工具回到 agent 继续决策 =====
    workflow.add_edge("execute_tool", "agent")

    return workflow