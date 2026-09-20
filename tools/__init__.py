"""
# what this block
# Import every tool module so its @tool-decorated functions register
# themselves on import, then export the populated registry.
# why this code
# `from tools import registry` (done once, from agent/core.py) is enough to
# load the entire tool catalog.
# optional if u want
# Order here becomes tool order in the system prompt / schema list.
"""
from . import (
    memory_tools,
    terminal_tool,
    file_tools,
    skill_tools,
    web_tools,
    delegate_tool,
    cron_tool,
    git_tool,
    notification_tool,
    voice_tool,
    meta_tools,
    learning_graph_tool,
)
from .registry import registry, ToolRegistry, tool

__all__ = ["registry", "ToolRegistry", "tool"]
