"""
Lightweight MCP-style tool server for the Bank Email Automation System.

Implements core MCP concepts:
1. Tool Registry   — declares available tools with JSON schemas
2. Tool Discovery  — LLM/agent can list available tools
3. Tool Dispatcher — execute a tool by name with args

Inspired by Anthropic's Model Context Protocol (MCP).
Reference: https://modelcontextprotocol.io
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from utils.api_client import get_client
from utils.logger import get_logger

log = get_logger("mcp_server")


# ============================================================
# TOOL DEFINITION
# ============================================================

@dataclass
class Tool:
    """Represents an MCP tool with schema + callable."""
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]
    tags: list[str] = field(default_factory=list)


# ============================================================
# TOOL REGISTRY
# ============================================================

class MCPToolRegistry:
    """Registry of tools available to agents."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
        log.info("mcp_tool_registered", tool=tool.name)

    def list_tools(self) -> list[dict[str, Any]]:
        """Discovery API — returns JSON-schema definitions."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "tags": t.tags,
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatcher — execute a tool by name."""
        if name not in self._tools:
            return {"error": f"Tool '{name}' not found", "ok": False}

        tool = self._tools[name]
        log.info("mcp_tool_call", tool=name, args=args)
        try:
            result = tool.handler(**args)
            return {"ok": True, "tool": name, "result": result}
        except TypeError as e:
            return {"ok": False, "tool": name, "error": f"Invalid args: {e}"}
        except Exception as e:
            log.error("mcp_tool_error", tool=name, error=str(e))
            return {"ok": False, "tool": name, "error": str(e)}

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)


# ============================================================
# TOOL HANDLERS (wrap the API client)
# ============================================================

def _validate_account(account_number: str) -> dict:
    return get_client().validate_account(account_number)


def _validate_card(card_number: str) -> dict:
    return get_client().validate_card(card_number)


def _get_balance(account_number: str) -> dict:
    return get_client().get_account_balance(account_number)


def _get_card_transactions(card_number: str, limit: int = 5) -> dict:
    return get_client().get_card_transactions(card_number, limit=limit)


def _get_statement(account_number: str, period: str) -> dict:
    return get_client().get_statement(account_number, period)


# ============================================================
# DEFAULT REGISTRY (all banking tools)
# ============================================================

def build_default_registry() -> MCPToolRegistry:
    """Create and populate the default MCP registry with banking tools."""
    reg = MCPToolRegistry()

    reg.register(Tool(
        name="validate_account",
        description="Check if an account number exists and is active.",
        input_schema={
            "type": "object",
            "properties": {
                "account_number": {"type": "string", "description": "10-18 digit account number"},
            },
            "required": ["account_number"],
        },
        handler=_validate_account,
        tags=["account", "validation"],
    ))

    reg.register(Tool(
        name="validate_card",
        description="Check if a credit card number exists and is active.",
        input_schema={
            "type": "object",
            "properties": {
                "card_number": {"type": "string", "description": "13-19 digit card number"},
            },
            "required": ["card_number"],
        },
        handler=_validate_card,
        tags=["card", "validation"],
    ))

    reg.register(Tool(
        name="get_account_balance",
        description="Fetch current balance for an account.",
        input_schema={
            "type": "object",
            "properties": {
                "account_number": {"type": "string"},
            },
            "required": ["account_number"],
        },
        handler=_get_balance,
        tags=["account", "balance"],
    ))

    reg.register(Tool(
        name="get_card_transactions",
        description="Fetch last N credit card transactions.",
        input_schema={
            "type": "object",
            "properties": {
                "card_number": {"type": "string"},
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 50},
            },
            "required": ["card_number"],
        },
        handler=_get_card_transactions,
        tags=["card", "transactions"],
    ))

    reg.register(Tool(
        name="get_statement",
        description="Fetch account statement for a given period.",
        input_schema={
            "type": "object",
            "properties": {
                "account_number": {"type": "string"},
                "period": {"type": "string", "description": "e.g. 'April 2026' or '2026-04'"},
            },
            "required": ["account_number", "period"],
        },
        handler=_get_statement,
        tags=["account", "statement"],
    ))

    return reg


# ============================================================
# MCP SERVER
# ============================================================

class MCPServer:
    """High-level MCP server exposing banking tools."""

    def __init__(self):
        self.registry = build_default_registry()

    def discover(self) -> list[dict[str, Any]]:
        """List all tools (JSON-schema)."""
        return self.registry.list_tools()

    def invoke(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool."""
        return self.registry.call(tool_name, args)

    def describe(self) -> str:
        """Human-readable description of available tools."""
        lines = ["Available MCP Tools:", "=" * 50]
        for t in self.discover():
            lines.append(f"\n• {t['name']}")
            lines.append(f"  {t['description']}")
            lines.append(f"  Tags: {', '.join(t['tags'])}")
        return "\n".join(lines)


# ============================================================
# SINGLETON
# ============================================================

_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    global _server
    if _server is None:
        _server = MCPServer()
    return _server


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] MCP Server")
    print("=" * 60)

    server = get_mcp_server()

    # 1. Discovery
    print("\n[1] Tool Discovery:")
    tools = server.discover()
    for t in tools:
        print(f"    • {t['name']} — {t['description'][:50]}")

    # 2. Call a tool (validate_account)
    print("\n[2] Invoke 'validate_account':")
    result = server.invoke("validate_account", {"account_number": "1234567890"})
    print(f"    {json.dumps(result, indent=2, default=str)[:300]}")

    # 3. Invalid tool
    print("\n[3] Invoke unknown tool:")
    result = server.invoke("unknown_tool", {})
    print(f"    {result}")

    # 4. Describe
    print("\n[4] Describe:")
    print(server.describe())

    print("\n[DONE] MCP Server tests complete!")