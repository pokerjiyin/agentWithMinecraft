"""
Agent State定义---Langgraph状态机
"""
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """状态机结构"""

    # 对话历史，add_messages自动追加而非覆盖
    messages: Annotated[list[BaseMessage],add_messages]

    # 用户意图，chat（闲聊）或game（游戏指令）
    intent: str

    # 任务计划（游戏指令时的步骤列表）
    plan: list[str]

    # 当前执行到第几步
    current_step: int

    # RAG 检索到的知识上下文
    rag_context: str

    # 游戏角色当前状态（JSON 字符串）
    game_state: str

    # 是否任务完成
    task_completed: bool
