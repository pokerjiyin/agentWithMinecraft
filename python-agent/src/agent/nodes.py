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
    model = settings.qwen_chat_model,
    api_key = settings.qwen_api_key,
    base_url = settings.qwen_base_url,
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

# ===== ReAct Agent 节点 =====

MAX_ITERATIONS = 15  # 最多 15 轮，防止死循环

async def agent(state: AgentState) -> dict:
    """
    ReAct 循环的"思考"节点
    看对话历史 + RAG 知识，决定下一步：调工具 or 结束
    """
    iterations = state.get("iterations", 0)
    if iterations >= MAX_ITERATIONS:
        # 超过上限，强制结束
        return {
            "messages": [AIMessage(content="任务步骤过多，已自动终止")],
            "iterations": iterations,
        }

    rag = state.get("rag_context", "")

    # 取最近 6 条消息作为上下文（防止历史无限膨胀）
    history = state["messages"][-6:]
    history_text = "\n".join(f"{'用户' if m.type == 'human' else 'AI'}: {m.content}" for m in history)
    prompt = f"""你是 Minecraft AI 操控智能体。根据对话历史决定下一步动作。

  RAG 知识：
  {rag}

  最近对话：
  {history_text}

  可用工具（只能选这些）：
  - move(x, y, z)            移动到绝对坐标
  - dig(x, y, z)             挖掘方块
  - chop_tree(x, y, z)       砍树
  - craft(recipe, count)     合成物品
  - use(action, target, itemName)  使用物品
  - open_chest(x, y, z)      打开箱子
  - get_status()             获取当前位置/血量/背包
  - get_inventory()          获取背包

  规则：
  1. 需要操作游戏时，调用对应工具
  2. 不知道坐标/材料时，先调用 get_status() 或 get_inventory()
  3. 工具的结果会在下一轮喂给你，基于结果继续决策
  4. 任务完成或无法继续时，输出最终回答

  只输出一个 JSON，不要其他内容：
  - 调工具：{{"tool": "move", "params": {{"x": 100, "y": 64, "z": 200}}}}
  - 完成任务：{{"answer": "你的回复"}}"""

    response = await llm.ainvoke(prompt)
    return {
        "messages": [AIMessage(content=response.content)],
        "iterations": iterations + 1,
    }

async def execute_tool(state: AgentState) -> dict:
    """
    ReAct 循环的"执行"节点
    解析 agent 输出的工具调用，执行，把结果作为观察塞回对话
    """
    # 取最后一条 AI 决策
    last_ai = state["messages"][-1]

    try:
        data = json.loads(last_ai.content)
        tool = data.get("tool")
        params = data.get("params", {})
    except (json.JSONDecodeError, TypeError):
        return {
            "messages": [HumanMessage(content="解析失败，请重新决策")],
        }

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
        try:
            result = await tool_map[tool](**params)
            observation = f"工具 {tool} 执行结果: {result}"
        except Exception as e:
            observation = f"工具 {tool} 执行失败: {e}"
    else:
        observation = f"未知工具: {tool}，请重新选择"
    # 观察结果以 HumanMessage 喂回给 agent
    return {
        "messages": [HumanMessage(content=observation)]
    }
