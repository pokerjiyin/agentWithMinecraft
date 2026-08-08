"""
Agent State定义---Langgraph状态机
"""
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """ReAct 状态机结构"""

    # 对话历史（用户消息、AI决策、工具观察结果，全部追加）
    messages: Annotated[list[BaseMessage], add_messages]

    # 用户意图，chat（闲聊）或game（游戏指令）
    intent: str

    # RAG 检索到的知识上下文
    rag_context: str

    # 循环次数（防止死循环）
    iterations: int
