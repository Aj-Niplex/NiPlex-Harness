"""Push notification tool. Optional — needs NTFY_TOPIC."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "send_notification", "description": "Send a push notification outside of chat", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}, "priority": {"type": "string", "enum": ["min", "low", "default", "high", "urgent"], "default": "default"}}, "required": ["title", "message"]}}})
def send_notification(agent: Any, args: Dict[str, Any]) -> str:
    try:
        import notifications
        return notifications.send_notification(args.get("title", ""), args.get("message", ""), args.get("priority", "default"))
    except ImportError:
        from config import cfg
        if not cfg.ntfy_topic:
            return "Notifications not configured. Set NTFY_TOPIC in .env."
        return "notifications package not present in this build."
