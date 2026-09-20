"""Scheduled-jobs category tools."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "add_cron_job", "description": "Add a scheduled job. schedule: 'every Nh', 'every Nm', or 'daily HH:MM' (UTC).", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "schedule": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["name", "schedule", "prompt"]}}})
def add_cron_job(agent: Any, args: Dict[str, Any]) -> str:
    return agent.cron.add_job(args.get("name", ""), args.get("schedule", ""), args.get("prompt", ""), session_id=agent.session_id)


@tool({"type": "function", "function": {"name": "list_cron_jobs", "description": "List cron", "parameters": {"type": "object", "properties": {}}}})
def list_cron_jobs(agent: Any, args: Dict[str, Any]) -> str:
    return agent.cron.list_jobs()


@tool({"type": "function", "function": {"name": "remove_cron_job", "description": "Remove cron", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}}})
def remove_cron_job(agent: Any, args: Dict[str, Any]) -> str:
    return agent.cron.remove_job(args.get("job_id", ""))
