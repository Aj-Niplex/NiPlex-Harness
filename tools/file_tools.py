"""Files & vault category tools."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "create_folder", "description": "Create a folder (required before putting files). Never write bare root files.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}})
def create_folder(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.create_folder(args.get("path", ""))


@tool({"type": "function", "function": {"name": "create_file", "description": "Create file inside a folder (e.g. vault/note.md). Not on root.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path"]}}})
def create_file(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.create_file(args.get("path", ""), args.get("content", ""))


@tool({"type": "function", "function": {"name": "edit_file", "description": "Overwrite file inside a folder", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}})
def edit_file(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.edit_file(args.get("path", ""), args.get("content", ""))


@tool({"type": "function", "function": {"name": "edit_selected_part", "description": "Replace exact text in a file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}})
def edit_selected_part(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.edit_selected_part(args.get("path", ""), args.get("old_text", ""), args.get("new_text", ""))


@tool({"type": "function", "function": {"name": "delete_file", "description": "Delete non-core file inside a folder", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}})
def delete_file(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.delete_file(args.get("path", ""))


@tool({"type": "function", "function": {"name": "list_files", "description": "List directory (default vault)", "parameters": {"type": "object", "properties": {"directory": {"type": "string", "default": "vault"}}}}})
def list_files(agent: Any, args: Dict[str, Any]) -> str:
    return agent.files.list_files(args.get("directory", "vault"))


@tool({"type": "function", "function": {"name": "send_file", "description": "Send file to user in chat", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "filename": {"type": "string"}}, "required": ["path"]}}})
def send_file(agent: Any, args: Dict[str, Any]) -> str:
    return agent._queue_file(args.get("path", ""), args.get("filename", ""))
