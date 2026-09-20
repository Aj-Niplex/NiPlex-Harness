"""Skills category tools."""
from __future__ import annotations
from typing import Any, Dict

import websearch
from tools.registry import tool


@tool({"type": "function", "function": {"name": "get_super_skill", "description": "Super Skill registry", "parameters": {"type": "object", "properties": {}}}})
def get_super_skill(agent: Any, args: Dict[str, Any]) -> str:
    return agent.skills.get_super_skill()


@tool({"type": "function", "function": {"name": "list_skills", "description": "List skills across personal/market/custom", "parameters": {"type": "object", "properties": {}}}})
def list_skills(agent: Any, args: Dict[str, Any]) -> str:
    return ", ".join(agent.skills.list_skills()) or "none"


@tool({"type": "function", "function": {"name": "load_skill", "description": "Load skill by name", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}})
def load_skill(agent: Any, args: Dict[str, Any]) -> str:
    return agent.skills.load_skill(args.get("name", ""))


@tool({"type": "function", "function": {"name": "create_skill", "description": "Create a new skill", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}, "use_case": {"type": "string"}, "category": {"type": "string", "enum": ["personal", "market", "custom"], "default": "personal"}}, "required": ["name", "content"]}}})
def create_skill(agent: Any, args: Dict[str, Any]) -> str:
    return agent.skills.create_skill(
        args.get("name", ""),
        args.get("content", ""),
        args.get("use_case", ""),
        args.get("category", "personal"),
    )


@tool({"type": "function", "function": {"name": "edit_skill", "description": "Edit an existing skill", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}}, "required": ["name", "content"]}}})
def edit_skill(agent: Any, args: Dict[str, Any]) -> str:
    return agent.skills.edit_skill(args.get("name", ""), args.get("content", ""))


@tool({"type": "function", "function": {"name": "search_skill", "description": "Search skills", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}})
def search_skill(agent: Any, args: Dict[str, Any]) -> str:
    return agent.skills.search_skill(args.get("query", ""))


@tool({"type": "function", "function": {"name": "search_web_or_github_for_skill", "description": "Web search for skill ideas", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}})
def search_web_or_github_for_skill(agent: Any, args: Dict[str, Any]) -> str:
    return websearch.web_search(args.get("query", ""))
