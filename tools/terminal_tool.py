"""Terminal / code-execution category tools."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "start_new_terminal", "description": "Start terminal", "parameters": {"type": "object", "properties": {"name": {"type": "string", "default": "main"}}}}})
def start_new_terminal(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.start_new_terminal(args.get("name", "main"))


@tool({"type": "function", "function": {"name": "run_code", "description": "Run Python; risky code needs button approval", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "terminal_id": {"type": "string"}}, "required": ["code"]}}})
def run_code(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.run_code(args.get("code", ""), args.get("terminal_id"))


@tool({"type": "function", "function": {"name": "get_results", "description": "Terminal results", "parameters": {"type": "object", "properties": {"terminal_id": {"type": "string"}, "last_n": {"type": "integer", "default": 5}}, "required": ["terminal_id"]}}})
def get_results(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.get_results(args.get("terminal_id", ""), args.get("last_n", 5))


@tool({"type": "function", "function": {"name": "set_terminal_lifecycle", "description": "kill|keep_alive|reset_history", "parameters": {"type": "object", "properties": {"terminal_id": {"type": "string"}, "action": {"type": "string", "enum": ["kill", "keep_alive", "reset_history"]}}, "required": ["terminal_id", "action"]}}})
def set_terminal_lifecycle(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.set_terminal_lifecycle(args.get("terminal_id", ""), args.get("action", ""))


@tool({"type": "function", "function": {"name": "list_terminals", "description": "List terminals", "parameters": {"type": "object", "properties": {}}}})
def list_terminals(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.list_terminals()


@tool({"type": "function", "function": {"name": "reset_sandbox_venv", "description": "Wipe the sandbox's dedicated venv", "parameters": {"type": "object", "properties": {}}}})
def reset_sandbox_venv(agent: Any, args: Dict[str, Any]) -> str:
    return agent.terminal.reset_sandbox()
