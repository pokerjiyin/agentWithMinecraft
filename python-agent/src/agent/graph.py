"""
LangGraph StateGraph 构建
定义节点 + 条件边 = 完整的 Agent 决策流
"""


from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    analyze_intent,
    chat_reply,
    rag_retrieve,
    plan_task,
    execute_step,
    check_completion,
)


def build_graph():
    """
    构建并编译 LangGraph StateGraph

  # 流程图：
  #     analyze_intent
  #        ├── "chat"  → chat_reply → END
  #        └── "game"  → rag_retrieve → plan_task → execute_step
  #                         ↑                               │
  #                         └─── check_completion ──────────┘
  #                              (未完成时重新规划)
    """
    workflow = StateGraph(AgentState)

    # ===== 添加节点 =====
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("chat_reply", chat_reply)
    workflow.add_node("rag_retrieve", rag_retrieve)
    workflow.add_node("plan_task", plan_task)
    workflow.add_node("execute_step", execute_step)
    workflow.add_node("check_completion", check_completion)

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
    workflow.add_edge("rag_retrieve","plan_task")
    workflow.add_edge("plan_task","execute_step")

    # ===== 条件边：继续 or 结束 =====
    def route_completion(state: AgentState) -> str:
        completed = state.get("task_completed",False)
        return "end" if completed else "continue"

    workflow.add_conditional_edges(
        "execute_step",
        route_completion,
        {
            "end": END,
            "continue": "check_completion",
        }
    )

    # ===== 未完成：回到规划 =====
    workflow.add_edge("check_completion","plan_task")

    # ===== 编译 =====
    return workflow.compile()