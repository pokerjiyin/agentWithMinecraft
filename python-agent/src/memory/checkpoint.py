"""
LangGraph Checkpoint 记忆持久化
使用 AsyncSqliteSaver 将对话状态保存到 SQLite
"""
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from ..config.settings import settings


async def get_checkpointer() -> AsyncSqliteSaver:
    """创建异步 SQLite Checkpoint 实例"""
    conn = await aiosqlite.connect(settings.checkpoint_db_path)
    return AsyncSqliteSaver(conn)
