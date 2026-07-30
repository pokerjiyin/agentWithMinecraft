"""
LangGraph 节点实现 —— 每个节点是一个独立的处理函数
"""


from langchain_core.messages import HumanMessage,AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from ..config.settings import settings

"""LLM实例（所有节点共享）"""
llm = ChatOpenAI(
    model = settings.llm_model,
    api_key = settings.deepseek_api_key,
    base_url = settings.deepseek_base_url,
    temperature = 0.7,
)

def analyze_intent(state: AgentState) -> dict:
    """
      节点 1：意图识别
      判断用户输入是闲聊还是游戏指令
    """
    last_message = state["messages"][-1].content

    prompt = f"""判断以下用户消息的意图，只回复"chat"或"game":
- "chat": 闲聊、问候、非游戏操作类对话
- "game": Minecraft 游戏操作指令（如移动、挖掘、合成、建造等）
用户消息: {last_message}
意图: """

    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    return {"intent": intent}

def chat_reply(state: AgentState) -> dict:
    """
      节点 2a：闲聊模式 → 直接回复用户
    """
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def rag_retrieve(state: AgentState) -> dict:
    """
      节点 2b：游戏指令 → 调用 Java RAG API 检索知识
    """
    last_message = state["messages"][-1].content

    # TODO: 阶段三完成后改为真实 HTTP 调用 JavaTool.rag_search()
    placeHolder = (
        f"[RAG占位]关于'{last_message}'的Minecraft知识"
        f"将在阶段三从Java RAG API获取"
    )

    return {"rag_context": placeHolder}

def plan_task(state: AgentState) -> dict:
    """
    节点 3：任务规划
    根据 RAG 上下文，将用户指令拆解为具体步骤
    """
    user_msg = state["messages"][-1].content
    rag = state.get("rag_context","")

    prompt = f"""你是 Minecraft 任务规划器。根据以下信息，将用户指令拆解为具体执行步骤。

  RAG 知识：{rag}

  用户指令：{user_msg}

  请列出执行步骤，每行一个步骤，格式：
  1. 第一步
  2. 第二步
  ...

  只需要列出步骤，不要其他解释。"""

    response = llm.invoke(prompt)
    lines = response.content.strip().split("\n")
    plan = [
        line.split(". ",1)[1] if". " in line else line
        for line in lines
        if line.strip()
    ]

    return {"plan": plan,"current_step": 0}

def execute_step(state: AgentState) -> dict:
    """
    节点 4：执行单个步骤
    调用 Java 工具 API 执行当前步骤
    （阶段三完成前，LLM 模拟执行结果）
    """
    plan = state.get("plan",[])
    step_idx = state.get("current_step",0)

    if step_idx >= len(plan):
        return {"task_completed": True}

    current_action = plan[step_idx]

    # TODO: 阶段三完成后改为真实 Java API 调用
    ai_msg = AIMessage(
        content=(
            f"[模拟执行] 步骤 {step_idx + 1}/{len(plan)}："
            f"{current_action} ✓ 完成"
        )
    )

    return {
        "messages": [ai_msg],
        "current_step": step_idx + 1,
    }

def check_completion(state: AgentState) -> dict:
    """
    节点 5：检查任务是否完成
    """
    plan = state.get("plan",[])
    step_idx = state.get("current_step",0)

    if step_idx >= len(plan):
        return {"task_completed": True}

    return{
        "task_completed": False,
        "messages": [
            HumanMessage(
                content=f"继续执行步骤 {step_idx + 1}：{plan[step_idx]}"
            )
        ],
    }