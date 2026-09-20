"""
# what this block
# Tool categories: groups of tools the model can see, each toggleable.
# why this code
# Users can disable whole categories (e.g. git, voice). When OFF, the model
# is told the category exists and how to turn it on, but never sees the
# individual tool schemas inside it.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from config import cfg

SETTINGS_PATH = cfg.data_dir / "tool_categories.json"


@dataclass
class ToolCategory:
    key: str
    label: str
    public_description: str
    default_enabled: bool
    tool_names: List[str]


CATEGORIES: Dict[str, ToolCategory] = {
    "memory": ToolCategory(
        key="memory", label="Memory",
        public_description="Save/search durable notes, a small knowledge graph, keyword-style vector search, and an auto-computed skill<->memory learning graph.",
        default_enabled=True,
        tool_names=["save_memory", "search_memory", "list_memory", "graph_add_node", "graph_add_edge", "graph_query", "vector_search", "get_learning_graph"],
    ),
    "terminal": ToolCategory(
        key="terminal", label="Terminal / code execution",
        public_description="Run Python in a sandboxed venv, manage terminal sessions, reset the sandbox.",
        default_enabled=True,
        tool_names=["start_new_terminal", "run_code", "get_results", "set_terminal_lifecycle", "list_terminals", "reset_sandbox_venv"],
    ),
    "files": ToolCategory(
        key="files", label="Files & vault",
        public_description="Create, edit, delete, and list files inside the vault/workspace, and send files to you.",
        default_enabled=True,
        tool_names=["create_folder", "create_file", "edit_file", "edit_selected_part", "delete_file", "list_files", "send_file"],
    ),
    "skills": ToolCategory(
        key="skills", label="Skills",
        public_description="List, load, write, and search the agent's own reusable skill files.",
        default_enabled=True,
        tool_names=["get_super_skill", "list_skills", "load_skill", "create_skill", "edit_skill", "search_skill"],
    ),
    "web": ToolCategory(
        key="web", label="Web search & page reading",
        public_description="Search the web and fetch/read a specific page's content.",
        default_enabled=True,
        tool_names=["web_search", "web_read", "search_web_or_github_for_skill"],
    ),
    "cron": ToolCategory(
        key="cron", label="Scheduled jobs",
        public_description="Store and list scheduled/cron-style jobs for later.",
        default_enabled=True,
        tool_names=["add_cron_job", "list_cron_jobs", "remove_cron_job"],
    ),
    "subagents": ToolCategory(
        key="subagents", label="Sub-agents",
        public_description="Spawn a named sub-agent for a sub-goal and collect its report.",
        default_enabled=True,
        tool_names=["spawn_subagent", "list_subagents", "subagent_report"],
    ),
    "git": ToolCategory(
        key="git", label="Git / GitHub",
        public_description="Read and manage your GitHub repos: list repos, read files, list/create issues, list commits.",
        default_enabled=False,
        tool_names=["git_list_repos", "git_list_files", "git_read_file", "git_list_issues", "git_create_issue", "git_list_commits"],
    ),
    "notifications": ToolCategory(
        key="notifications", label="Push notifications",
        public_description="Send yourself a push notification outside of chat (e.g. when a background job finishes).",
        default_enabled=True,
        tool_names=["send_notification"],
    ),
    "voice": ToolCategory(
        key="voice", label="Voice (text-to-speech)",
        public_description="Speak a reply out loud as a voice message, using a locally-run offline voice (Piper).",
        default_enabled=False,
        tool_names=["speak", "set_voice"],
    ),
}

ALWAYS_ON_TOOLS = {"who_am_i", "report_status", "get_progress", "list_tool_categories", "set_tool_category"}


def _load_settings() -> Dict[str, bool]:
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {k: bool(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_settings(settings: Dict[str, bool]) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except Exception:
        pass


class CapabilityManager:
    def __init__(self):
        stored = _load_settings()
        self.enabled: Dict[str, bool] = {
            key: stored.get(key, cat.default_enabled) for key, cat in CATEGORIES.items()
        }

    def is_enabled(self, category_key: str) -> bool:
        return self.enabled.get(category_key, False)

    def set_enabled(self, category_key: str, enabled: bool) -> str:
        if category_key not in CATEGORIES:
            valid = ", ".join(CATEGORIES.keys())
            return f"Unknown category '{category_key}'. Valid categories: {valid}"
        self.enabled[category_key] = enabled
        _save_settings(self.enabled)
        state = "enabled" if enabled else "disabled"
        return f"'{CATEGORIES[category_key].label}' is now {state}."

    def category_for_tool(self, tool_name: str) -> Optional[str]:
        for key, cat in CATEGORIES.items():
            if tool_name in cat.tool_names:
                return key
        return None

    def is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name in ALWAYS_ON_TOOLS:
            return True
        cat_key = self.category_for_tool(tool_name)
        if cat_key is None:
            return True
        return self.is_enabled(cat_key)

    def manifest_for_prompt(self) -> str:
        lines = []
        for key, cat in CATEGORIES.items():
            state = "ON" if self.is_enabled(key) else "OFF"
            lines.append(f"- {cat.label} (key: {key}) [{state}]: {cat.public_description}")
        return "\n".join(lines)

    def list_categories(self) -> str:
        return self.manifest_for_prompt()
