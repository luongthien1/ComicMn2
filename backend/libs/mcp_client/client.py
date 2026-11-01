"""Quản lý 1 MCP ClientSession persistent tới comic-graphrag-mcp (stdio transport).

Backend spawn MCP server làm subprocess lúc FastAPI startup (xem lifespan trong main.py)
và giữ session này xuyên suốt vòng đời app.
"""

import json
from contextlib import AsyncExitStack
from typing import Any, Optional

from core.config import settings
from libs.logger.log import get_logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = get_logger(__name__)


class McpClientError(Exception):
    pass


class McpClientManager:
    def __init__(self):
        self._stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None

    async def start(self):
        if not settings.MCP_SERVER_PYTHON or not settings.MCP_SERVER_CWD:
            logger.warning(
                "MCP_SERVER_PYTHON/MCP_SERVER_CWD chưa cấu hình — bỏ qua khởi động comic-graphrag-mcp."
            )
            return

        params = StdioServerParameters(
            command=settings.MCP_SERVER_PYTHON,
            args=["-m", "comic_graphrag_mcp.server"],
            cwd=settings.MCP_SERVER_CWD,
        )

        self._stack = AsyncExitStack()
        try:
            read, write = await self._stack.enter_async_context(stdio_client(params))
            self._session = await self._stack.enter_async_context(ClientSession(read, write))
            await self._session.initialize()
            logger.info("Da ket noi comic-graphrag-mcp qua stdio.")
        except Exception:
            logger.exception("Không khởi động được comic-graphrag-mcp subprocess.")
            await self._stack.aclose()
            self._stack = None
            self._session = None

    async def stop(self):
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self._session = None

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if self._session is None:
            raise McpClientError(
                "comic-graphrag-mcp chưa kết nối (kiểm tra MCP_SERVER_PYTHON/MCP_SERVER_CWD trong .env)."
            )
        result = await self._session.call_tool(name, arguments)
        if result.isError:
            text = "".join(c.text for c in result.content if hasattr(c, "text"))
            raise McpClientError(text or "Lỗi không xác định từ comic-graphrag-mcp")

        text_parts = [c.text for c in result.content if hasattr(c, "text")]
        if not text_parts:
            return None
        raw = text_parts[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


mcp_client = McpClientManager()
