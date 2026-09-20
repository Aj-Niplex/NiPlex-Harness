"""
# what this block
# Core agent loop for NiPlex Agent on NiPlex Harness.
# why this code
# Tools + provider loop; identity loaded from soul.md; tool categories are
# toggleable (see agent/capabilities.py); files never on root. Tool schemas
# and dispatch live in tools/ registry — this module asks the registry for
# schemas + dispatch.
# optional if u want
# Raise tool-loop rounds only if you need deeper multi-step tool use.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.capabilities import CapabilityManager, CATEGORIES
from agent.identity import get_identity_block
from agent.providers import get_provider
from agent.status import StatusChannel
from agent.subagents import SubAgentManager
from memory import MemoryManager
from terminal import TerminalManager
from skills.manager import SkillManager
from files import FileManager
from cron import CronManager
from tools import registry as tool_registry

logger = logging.getLogger("niplex.agent")

SYSTEM_TEMPLATE = """{identity_block}

Capabilities are grouped into toggleable categories. Current state:
{capability_manifest}

A category marked OFF has no tools visible to you right now — you don't
see their names or parameters, only that the category exists and what it's
for. If something the user wants clearly needs a disabled category, tell
them plainly and say they can ask you to turn it on (set_tool_category) —
never guess at what might be inside it.

File rules:
- Never put a file on the project root. Create a folder first, then write inside it.
- Prefer vault/ for Obsidian-ready Markdown the user can open and edit.
- Core harness paths cannot be deleted or overwritten.

Current memory context:
{memory_context}

Platform username of whoever is currently messaging: {platform_username}
This is a verified technical fact from the chat platform itself — separate
from any "real name" the person may have, which only comes from what they
tell you or from memory. Don't conflate the two.

Rules:
1. Prefer tools over guessing.
2. Keep replies mobile-friendly.
3. If code needs approval, tell the user to use the buttons (not slash commands).
4. When a tool informed your answer, briefly say so in the reply itself — which
   tool, what you looked up or ran — instead of a flat conclusion with no
   indication of how you got there. A sentence is enough; do not withhold this
   only to reveal it if asked.
"""

HISTORY_SOFT_LIMIT = 40
HISTORY_TARGET = 32


class Agent:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.memory = MemoryManager(session_id)
        self.terminal = TerminalManager(session_id=self.session_id)
        self.skills = SkillManager()
        self.files = FileManager()
        self.status = StatusChannel()
        self.subagents = SubAgentManager()
        self.cron = CronManager()
        self.capabilities = CapabilityManager()
        self.provider = get_provider()
        self.history: List[Dict[str, Any]] = []
        self.outbound_files: List[Dict[str, str]] = []

    def _active_tools(self) -> List[Dict[str, Any]]:
        return [t for t in tool_registry.schemas() if self.capabilities.is_tool_allowed(t["function"]["name"])]

    def _system_prompt(self, platform_username: Optional[str] = None) -> str:
        ctx = self.memory.get_context_for_prompt()
        return SYSTEM_TEMPLATE.format(
            identity_block=get_identity_block(),
            capability_manifest=self.capabilities.manifest_for_prompt(),
            memory_context=ctx or "(empty)",
            platform_username=platform_username or "(not provided by this gateway)",
        )

    def _queue_file(self, path: str, filename: str = "") -> str:
        if self.files._is_protected(path):
            return f"HARD BLOCK: cannot send protected file: {path}"

        try:
            self.files._resolve(path)
        except Exception:
            return f"HARD BLOCK: path escapes project root: {path}"

        p = Path(path)
        if not p.exists() or not p.is_file():
            return f"File not found: {path}"
        if p.name in (".env", ".git-credentials") or p.suffix in (".pem", ".key"):
            return f"Refusing to send secret-looking file: {p.name}"
        self.outbound_files.append({"path": str(p), "filename": filename or p.name})
        return f"Queued {filename or p.name} to send to the user."

    def _dispatch_tool(self, name: str, args: Dict[str, Any]) -> str:
        if not self.capabilities.is_tool_allowed(name):
            cat_key = self.capabilities.category_for_tool(name)
            label = CATEGORIES[cat_key].label if cat_key in CATEGORIES else name
            return f"'{label}' is currently disabled. Ask the user if they want it turned on."
        try:
            return tool_registry.dispatch(name, self, args)
        except Exception as e:
            logger.exception("Tool error")
            return f"Tool error: {type(e).__name__}"

    def _trim_history(self) -> None:
        if len(self.history) <= HISTORY_SOFT_LIMIT:
            return
        cut_from = len(self.history) - HISTORY_TARGET
        for i in range(cut_from, len(self.history)):
            if self.history[i].get("role") == "user":
                self.history = self.history[i:]
                return

    def chat(
        self,
        user_message: str,
        platform_username: Optional[str] = None,
        tools_override: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        self.history.append({"role": "user", "content": user_message})
        tools = tools_override if tools_override is not None else self._active_tools()
        restricted_names = (
            {t["function"]["name"] for t in tools_override} if tools_override is not None else None
        )
        messages = [{"role": "system", "content": self._system_prompt(platform_username)}] + self.history
        try:
            response = self.provider.chat(messages, tools=tools)
            for _ in range(8):
                tool_calls = response.get("tool_calls")
                if not tool_calls:
                    break
                self.history.append(response)
                for tc in tool_calls:
                    fn = tc["function"]
                    name = fn["name"]
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    if restricted_names is not None and name not in restricted_names:
                        result = f"'{name}' is not available in this restricted context."
                    else:
                        result = self._dispatch_tool(name, args)
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", name),
                        "content": result,
                    })
                tools = tools_override if tools_override is not None else self._active_tools()
                messages = [{"role": "system", "content": self._system_prompt(platform_username)}] + self.history
                response = self.provider.chat(messages, tools=tools)
            final = response.get("content") or "(no response)"
        except Exception as e:
            logger.exception("Chat error")
            final = f"Error: {type(e).__name__}"
        self.history.append({"role": "assistant", "content": final})
        self._trim_history()
        return final
