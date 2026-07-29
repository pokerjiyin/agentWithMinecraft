"""
应用配置 —— 从 .env 文件和环境变量读取
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """全局配置单例"""

    # ===== DeepSeek =====
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "sk-xxx")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    deepseek_base_url: str = "https://api.deepseek.com/anthropic"

    # ===== ChromaDB =====
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))

    # ===== Java Service =====
    java_service_url: str = os.getenv(
        "JAVA_SERVICE_URL", "http://localhost:8081"
    )

    # ===== Agent =====
    agent_port: int = int(os.getenv("AGENT_PORT", "8000"))

    # ===== Checkpoint 数据库 =====
    checkpoint_db_path: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "checkpoints.db",
    )


settings = Settings()
