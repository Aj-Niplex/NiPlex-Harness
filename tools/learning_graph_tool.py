"""Learning graph introspection tool."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "get_learning_graph", "description": "See skills connected to memory with usage stats", "parameters": {"type": "object", "properties": {}}}})
def get_learning_graph(agent: Any, args: Dict[str, Any]) -> str:
    try:
        from agent.learning_graph import build_learning_graph, render_summary
        graph = build_learning_graph()
        return render_summary(graph)
    except ImportError:
        return "Learning graph not available in this build."
