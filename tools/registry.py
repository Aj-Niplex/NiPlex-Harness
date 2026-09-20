"""
# what this block
# Central tool registry — every tool module self-registers its OpenAI-style
# function schema + handler here instead of agent/core.py hard-coding one
# giant TOOLS list and one giant if/elif dispatch chain.
# why this code
# Phase 0 of the Hermes-inspired restructure. Adding a new tool becomes
# "write one file + register it in tools/__init__.py" instead of touching
# agent/core.py. No behavior change vs the old inline TOOLS list — schemas
# and dispatch bodies were relocated verbatim, not rewritten.
# optional if u want
# Handlers take (agent, args) so they can reach agent.memory, agent.files,
# agent.session_id, etc.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List

ToolHandler = Callable[[Any, Dict[str, Any]], str]


class ToolRegistry:
    """Holds every tool's schema + handler, keyed by tool name."""

    def __init__(self) -> None:
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, ToolHandler] = {}
        self._order: List[str] = []  # registration order -> stable prompt/tool ordering

    def register(self, schema: Dict[str, Any], handler: ToolHandler) -> None:
        name = schema["function"]["name"]
        if name in self._schemas:
            raise ValueError(f"Tool '{name}' is already registered")
        self._schemas[name] = schema
        self._handlers[name] = handler
        self._order.append(name)

    def schemas(self) -> List[Dict[str, Any]]:
        """Full catalog, in registration order. Category filtering still
        happens in agent/core.py against CapabilityManager."""
        return [self._schemas[name] for name in self._order]

    def names(self) -> List[str]:
        return list(self._order)

    def has(self, name: str) -> bool:
        return name in self._handlers

    def dispatch(self, name: str, agent: Any, args: Dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if handler is None:
            return f"Unknown tool: {name}"
        return handler(agent, args)


# One shared instance. Tool modules import `tool` (the decorator below) and
# register onto this at import time; agent/core.py imports `registry`.
registry = ToolRegistry()


def tool(schema: Dict[str, Any]):
    """Decorator for tool modules: `@tool({...schema...})` above a
    `handler(agent, args) -> str` function registers both in one call.

    Example:
        @tool({"type": "function", "function": {"name": "my_tool", ...}})
        def my_tool(agent, args):
            return agent.some_manager.do_thing(args.get("x"))
    """

    def _wrap(fn: ToolHandler) -> ToolHandler:
        registry.register(schema, fn)
        return fn

    return _wrap
