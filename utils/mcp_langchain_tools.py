"""
Bridge between MCP registry and LangChain tools.
Converts MCP tools into LangChain-compatible Tool objects.
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool

from utils.mcp_server import get_mcp_server
from utils.logger import get_logger

log = get_logger("mcp_langchain")


def get_langchain_tools() -> list[StructuredTool]:
    """
    Return all MCP tools as LangChain StructuredTools.
    Agents can bind these to an LLM for native tool-calling.
    """
    server = get_mcp_server()
    tools: list[StructuredTool] = []

    for spec in server.discover():
        name = spec["name"]
        description = spec["description"]

        # Create a closure to capture name correctly
        def _make_handler(tool_name: str):
            def _handler(**kwargs: Any) -> dict:
                return server.invoke(tool_name, kwargs)
            return _handler

        tool = StructuredTool.from_function(
            func=_make_handler(name),
            name=name,
            description=description,
        )
        tools.append(tool)

    log.info("langchain_tools_created", count=len(tools))
    return tools


if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] MCP → LangChain bridge")
    tools = get_langchain_tools()
    print(f"  Created {len(tools)} LangChain tools:")
    for t in tools:
        print(f"    • {t.name}: {t.description[:60]}")
    print("\n[DONE] MCP LangChain bridge ready!")