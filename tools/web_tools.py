"""Web category tools — DuckDuckGo search and page reading."""
from __future__ import annotations
from typing import Any, Dict

import websearch
from tools.registry import tool


@tool({"type": "function", "function": {"name": "web_search", "description": "DuckDuckGo search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query"]}}})
def web_search(agent: Any, args: Dict[str, Any]) -> str:
    return websearch.web_search(args.get("query", ""), args.get("max_results", 5))


@tool({"type": "function", "function": {"name": "web_read", "description": "Fetch and read a specific page's text content", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}})
def web_read(agent: Any, args: Dict[str, Any]) -> str:
    return websearch.web_read(args.get("url", ""))
