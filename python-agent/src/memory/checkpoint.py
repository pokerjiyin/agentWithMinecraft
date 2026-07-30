"""
LangGraph Checkpoint 记忆持久化
使用 SqliteSaver 将对话状态保存到 SQLite
"""


from langgraph.checkpoint.sqlite import SqliteSaver
from ..config.settings import settings


def get_checkpointer() -> SqliteSaver:
    """创建 SQLite Checkpoint 实例"""
    return SqliteSaver.from_conn_string(settings.checkpoint_db_path)