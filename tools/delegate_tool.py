"""Sub-agents category tools."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "spawn_subagent", "description": "Spawn sub-agent", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "goal": {"type": "string"}}, "required": ["name", "goal"]}}})
def spawn_subagent(agent: Any, args: Dict[str, Any]) -> str:
    return agent.subagents.spawn(args.get("name", ""), args.get("goal", ""), agent.session_id)


@tool({"type": "function", "function": {"name": "list_subagents", "description": "List sub-agents", "parameters": {"type": "object", "properties": {}}}})
def list_subagents(agent: Any, args: Dict[str, Any]) -> str:
    return agent.subagents.list_subagents()


@tool({"type": "function", "function": {"name": "subagent_report", "description": "Finish sub-agent", "parameters": {"type": "object", "properties": {"sub_id": {"type": "string"}, "result": {"type": "string"}}, "required": ["sub_id", "result"]}}})
def subagent_report(agent: Any, args: Dict[str, Any]) -> str:
    return agent.subagents.report_result(args.get("sub_id", ""), args.get("result", ""))
