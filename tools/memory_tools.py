"""Memory category tools — schemas + dispatch to agent.memory."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "save_memory", "description": "Save note. scope=global|session", "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "title": {"type": "string"}, "scope": {"type": "string", "enum": ["global", "session"]}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["content", "title", "scope"]}}})
def save_memory(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.save_memory(args.get("content", ""), args.get("title", "Note"), args.get("scope", "session"), args.get("tags"))


@tool({"type": "function", "function": {"name": "search_memory", "description": "Keyword search memory", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "scope": {"type": "string", "enum": ["global", "session", "both"], "default": "both"}}, "required": ["query"]}}})
def search_memory(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.search_memory(args.get("query", ""), args.get("scope", "both"))


@tool({"type": "function", "function": {"name": "list_memory", "description": "List memory files", "parameters": {"type": "object", "properties": {"scope": {"type": "string", "enum": ["global", "session", "both"], "default": "both"}}}}})
def list_memory(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.list_memory(args.get("scope", "both"))


@tool({"type": "function", "function": {"name": "graph_add_node", "description": "Add graph node", "parameters": {"type": "object", "properties": {"node_id": {"type": "string"}, "label": {"type": "string"}, "node_type": {"type": "string", "default": "note"}}, "required": ["node_id", "label"]}}})
def graph_add_node(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.graph_add_node(args.get("node_id", ""), args.get("label", ""), args.get("node_type", "note"))


@tool({"type": "function", "function": {"name": "graph_add_edge", "description": "Link graph nodes", "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "target": {"type": "string"}, "relation": {"type": "string", "default": "related"}}, "required": ["source", "target"]}}})
def graph_add_edge(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.graph_add_edge(args.get("source", ""), args.get("target", ""), args.get("relation", "related"))


@tool({"type": "function", "function": {"name": "graph_query", "description": "Query graph", "parameters": {"type": "object", "properties": {"node_id": {"type": "string"}}}}})
def graph_query(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.graph_query(args.get("node_id"))


@tool({"type": "function", "function": {"name": "vector_search", "description": "Semantic-style search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}}})
def vector_search(agent: Any, args: Dict[str, Any]) -> str:
    return agent.memory.vector_search(args.get("query", ""), args.get("limit", 5))
