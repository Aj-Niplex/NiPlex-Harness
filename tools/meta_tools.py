"""Always-on meta tools: identity, progress, category switches."""
from __future__ import annotations
from typing import Any, Dict

from agent.identity import get_identity_block, get_signature
from tools.registry import tool


@tool({"type": "function", "function": {"name": "who_am_i", "description": "Identity", "parameters": {"type": "object", "properties": {}}}})
def who_am_i(agent: Any, args: Dict[str, Any]) -> str:
    return get_identity_block() + "\n" + get_signature()


@tool({"type": "function", "function": {"name": "report_status", "description": "Progress note", "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}})
def report_status(agent: Any, args: Dict[str, Any]) -> str:
    return agent.status.report(args.get("message", ""))


@tool({"type": "function", "function": {"name": "get_progress", "description": "Get progress", "parameters": {"type": "object", "properties": {}}}})
def get_progress(agent: Any, args: Dict[str, Any]) -> str:
    return agent.status.get_progress()


@tool({"type": "function", "function": {"name": "list_tool_categories", "description": "Show which tool categories exist and whether each is ON or OFF", "parameters": {"type": "object", "properties": {}}}})
def list_tool_categories(agent: Any, args: Dict[str, Any]) -> str:
    return agent.capabilities.list_categories()


@tool({"type": "function", "function": {"name": "set_tool_category", "description": "Turn a tool category on or off", "parameters": {"type": "object", "properties": {"category": {"type": "string"}, "enabled": {"type": "boolean"}}, "required": ["category", "enabled"]}}})
def set_tool_category(agent: Any, args: Dict[str, Any]) -> str:
    return agent.capabilities.set_enabled(args.get("category", ""), bool(args.get("enabled")))
