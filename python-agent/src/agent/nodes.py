"""
LangGraph 节点实现 —— 每个节点是一个独立的处理函数
"""

import json
import logging
from langchain_core.messages import HumanMessage,AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from ..config.settings import settings
from ..tools.java_tools import java_tools

log = logging.getLogger(__name__)

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

    prompt = f"""判断以下用户消息的意图，只回复 "chat" 或 "game"，不要回复任何其他内容。

  - "chat"：问候、聊天、非操作类对话。例如："你好"、"今天天气不错"
  - "game"：Minecraft 游戏操作指令。例如："砍树"、"挖矿"、"造一把石剑"、"去坐标100,64,200"

  用户消息：{last_message}

  意图："""

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

async def rag_retrieve(state: AgentState) -> dict:
    """
      节点 2b：游戏指令 → 调用 Java RAG API 检索知识
    """
    last_message = state["messages"][-1].content

    try:
        result = await java_tools.rag_search(last_message)
        items= result.get("results", [])
        if items:
            rag_context = "\n---\n".join(
                item.get("content", "")[:500] for item in items
            )
        else:
            rag_context = "(知识库中未找到相关内容)"
    except Exception as e:
        log.warning(f"RAG 检索失败: {e}")
        rag_context = f"(RAG 服务暂不可用: {e})"

    return {"rag_context": rag_context}



async def plan_task(state: AgentState) -> dict:
    """
    节点 3：任务规划
    根据 RAG 上下文，将用户指令拆解为具体步骤
    仅首次调用时规划，循环回来时跳过
    """
    existing_plan = state.get("plan", [])
    if existing_plan:
        # 已有计划，不重规划，继续执行
        return {}

    user_msg = state["messages"][-1].content
    rag = state.get("rag_context", "")

    prompt = f"""你是 Minecraft 任务规划器。根据以下信息，将用户指令拆解为具体执行步骤。

  RAG 知识：{rag}

  用户指令：{user_msg}

  请列出执行步骤，每行一个步骤，格式：
  1. 第一步
  2. 第二步
  ...

  只需要列出步骤，不要其他解释。"""

    response = await llm.ainvoke(prompt)
    lines = response.content.strip().split("\n")
    plan = [
        line.split(". ", 1)[1] if ". " in line else line
        for line in lines
        if line.strip()
    ]

    return {"plan": plan, "current_step": 0}

async def execute_step(state: AgentState) -> dict:
    """
    节点 4：执行单个步骤
    调用 Java 工具 API 执行当前步骤
    """
    plan = state.get("plan",[])
    step_idx = state.get("current_step",0)

    if step_idx >= len(plan):
        return {"task_completed": True}

    current_action = plan[step_idx]

    # 让 LLM 把自然语言步骤解析成工具调用
    parse_prompt = f"""你是 Minecraft 指令解析器。将操作步骤转换为工具调用 JSON。

      可用工具：
      - move(x, y, z)          — 移动到坐标
      - dig(x, y, z)           — 挖掘方块
      - chop_tree(x, y, z)     — 砍树
      - craft(recipe, count)   — 合成物品
      - use(action, target, itemName) — 使用物品
      - open_chest(x, y, z)    — 打开箱子
      - get_status()           — 获取状态
      - get_inventory()        — 获取背包

      操作：{current_action}

      只返回 JSON，不要其他内容：
      {{"tool": "工具名", "params": {{"x": 1, "y": 2, "z": 3}}}}"""

    try:
        response = await llm.ainvoke(parse_prompt)
        tool_call = json.loads(response.content.strip())
        tool = tool_call.get("tool")
        params = tool_call.get("params", {})

        # 路由到对应的工具
        tool_map = {
            "move": java_tools.move,
            "dig": java_tools.dig,
            "chop_tree": java_tools.chop_tree,
            "craft": lambda **kw: java_tools.craft(
                kw.get("recipe", ""), kw.get("count", 1)
            ),
            "use": lambda **kw: java_tools.use(
                kw.get("action", ""), kw.get("target"), kw.get("itemName")
            ),
            "open_chest": java_tools.open_chest,
            "get_status": java_tools.get_status,
            "get_inventory": java_tools.get_inventory,
        }

        if tool in tool_map:
            result = await tool_map[tool](**params)
            msg = (
                f"[步骤 {step_idx + 1}/{len(plan)}] {current_action}\n"
                f"→ {tool} → {result.get('success', '执行完成')}"
            )
        else:
            msg = f"[步骤 {step_idx + 1}] {current_action} → 未知工具: {tool}"

    except(json.JSONDecodeError, KeyError):
        # LLM 返回格式不对，降级为模拟执行
        msg = (
            f"[模拟执行] 步骤 {step_idx + 1}/{len(plan)}："
            f"{current_action} ✓ 完成"
        )
    except Exception as e:
        msg = f"[步骤 {step_idx + 1}] {current_action} → 执行失败: {e}"

    ai_msg = AIMessage(content=msg)
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