"""
Java 业务中台 API 调用封装
Python Agent 通过 HTTP 调用 Java Service 的工具接口
"""


import httpx
from ..config.settings import settings

class JavaTools:
    """Java Service 的工具调用客户端"""

    def __init__(self):
        self.base_url = settings.java_service_url
        self.timeout = 30.0

    async def _post(self, path: str, body: dict) -> dict:
        """通用POST"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}{path}", json=body)
            resp.raise_for_status()
            return resp.json()

    async def _get(self, path: str) -> dict:
        """通用 GET"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}{path}")
            resp.raise_for_status()
            return resp.json()

    # ===== RAG =====
    async def rag_search(self, query: str,top_k: int = 5) -> dict:
        return await self._post("/api/rag/search",{
            "query": query,
            "top_k": top_k,
        })

    async def rag_index(self, documents: list) -> dict:
        return await self._post("/api/rag/index",{
            "documents": documents,
        })

    # ===== 游戏操控 =====
    async def move (self,x: float, y: float, z: float) -> dict:
        return await self._post("/api/tools/move",{"x": x, "y": y, "z": z})

    async def dig(self, x: int, y: int, z: int) -> dict:
        return await self._post("/api/tools/dig", {"x": x, "y": y, "z": z})

    async def chop_tree(self, x: int, y: int, z: int) -> dict:
        return await self._post("/api/tools/chop_tree", {"x": x, "y": y, "z": z})

    async def craft(self, recipe_name: str, count: int = 1) -> dict:
        return await self._post("/api/tools/craft", {
            "recipe": recipe_name,
            "count": count,
        })

    async def open_chest(self, x: int, y: int, z: int) -> dict:
        return await self._post("/api/tools/open_chest", {"x": x, "y": y, "z": z})

    async def use(self, action: str, target: dict = None,
                  item_name: str = None) -> dict:
        body = {"action": action}
        if target:
            body["target"] = target
        if item_name:
            body["itemName"] = item_name
        return await self._post("/api/tools/use", body)

    async def get_status(self) -> dict:
        return await self._get("/api/tools/status")

    async def get_inventory(self) -> dict:
        return await self._get("/api/tools/inventory")

java_tools = JavaTools()