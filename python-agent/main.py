"""
Minecraft AI Agent —— 入口
"""


import uvicorn
from src.config.settings import settings

def main():
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=settings.agent_port,
        reload=True,
    )

if __name__ == "__main__":
    main()