"""
# what this block
# File I/O rules for NiPlex Agent.
# why this code
# - Never write a file directly on repo root (must be inside a folder).
# - AI may create folders, then put files inside them.
# - Core harness paths are HARD BLOCK forever.
# - Preferred vault folder: vault/ (Obsidian-ready Markdown).
"""
from __future__ import annotations
from pathlib import Path

from config import cfg

DEFAULT_VAULT_NAME = "vault"

PROTECTED_PREFIXES = [
    "agent/", "gateway/", "security/", "sandbox/", "terminal/", "memory/",
    "mcp/", "cron/", "websearch/", "github_issues/", "files/", "skills/",
    "walkthrough/", "setup/",
    "tools/", "notifications/", "voice/", "git_tools/",
    "launch.py", "config.py", "requirements.txt", ".env", ".git/",
    "agent/identity.py", "agent/branding.py",
    "data/secrets_vault.json", "data/runtime_provider.json",
]


class PathEscapesRoot(PermissionError):
    """Raised internally when a path resolves outside the project root."""


class FileManager:
    def __init__(self):
        self.root = cfg.data_dir.parent
        vault = self.root / DEFAULT_VAULT_NAME
        vault.mkdir(exist_ok=True)
        readme = vault / "README.md"
        if not readme.exists():
            readme.write_text(
                "---\ntags: [vault]\n---\n\n"
                "# Vault\n\n"
                "This folder is an Obsidian-ready vault.\n"
                "Open this folder in Obsidian to browse and edit notes normally.\n"
                "NiPlex Agent stores working notes here as plain Markdown.\n",
                encoding="utf-8",
            )

    def _resolve(self, rel_path: str) -> Path:
        root_resolved = self.root.resolve()
        p = (self.root / rel_path).resolve()
        try:
            p.relative_to(root_resolved)
        except ValueError:
            raise PathEscapesRoot("Path escapes project root")
        return p

    def _rel_from_root(self, rel_path: str) -> str:
        p = self._resolve(rel_path)
        return p.relative_to(self.root.resolve()).as_posix()

    def _is_protected(self, rel_path: str) -> bool:
        try:
            rel = self._rel_from_root(rel_path)
        except PathEscapesRoot:
            return True
        for pref in PROTECTED_PREFIXES:
            if rel == pref.rstrip("/") or rel.startswith(pref):
                return True
        return False

    def _is_root_file(self, rel_path: str) -> bool:
        try:
            rel = self._rel_from_root(rel_path)
        except PathEscapesRoot:
            return False
        return "/" not in rel and rel != ""

    def create_folder(self, path: str) -> str:
        if self._is_protected(path):
            return f"HARD BLOCK: cannot create folder in core: {path}"
        try:
            p = self._resolve(path)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {path}"
        p.mkdir(parents=True, exist_ok=True)
        return f"Created folder {path}"

    def create_file(self, path: str, content: str = "") -> str:
        if self._is_protected(path):
            return f"HARD BLOCK: harness core cannot be written: {path}"
        if self._is_root_file(path):
            return (
                f"Refused: do not put files on root. "
                f"Create a folder first (e.g. vault/{path} or notes/{path})."
            )
        try:
            p = self._resolve(path)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {path}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Created {path} ({len(content)} bytes)"

    def edit_file(self, path: str, content: str) -> str:
        if self._is_protected(path):
            return f"HARD BLOCK: harness core cannot be edited: {path}"
        if self._is_root_file(path):
            return "Refused: root files cannot be edited by the agent."
        try:
            p = self._resolve(path)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {path}"
        if not p.exists():
            return f"File does not exist: {path}"
        p.write_text(content, encoding="utf-8")
        return f"Edited {path}"

    def edit_selected_part(self, path: str, old_text: str, new_text: str) -> str:
        if self._is_protected(path):
            return f"HARD BLOCK: harness core cannot be edited: {path}"
        if self._is_root_file(path):
            return "Refused: root files cannot be edited by the agent."
        try:
            p = self._resolve(path)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {path}"
        if not p.exists():
            return f"File not found: {path}"
        text = p.read_text(encoding="utf-8")
        if old_text not in text:
            return "old_text not found (exact match required)"
        if text.count(old_text) > 1:
            return "old_text appears multiple times; make it unique"
        p.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Replaced selected part in {path}"

    def delete_file(self, path: str) -> str:
        if self._is_protected(path):
            return f"HARD BLOCK: harness core can never be deleted: {path}"
        if self._is_root_file(path):
            return "Refused: root files cannot be deleted by the agent."
        try:
            p = self._resolve(path)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {path}"
        if not p.exists():
            return f"File not found: {path}"
        if p.is_dir():
            return "Refusing to delete directories via delete_file."
        p.unlink()
        return f"Deleted {path}"

    def list_files(self, directory: str = "vault") -> str:
        try:
            p = self._resolve(directory)
        except PathEscapesRoot:
            return f"HARD BLOCK: path escapes project root: {directory}"
        if not p.exists():
            return f"Directory not found: {directory}"
        items = []
        for child in sorted(p.iterdir()):
            kind = "DIR " if child.is_dir() else "FILE"
            items.append(f"{kind}  {child.relative_to(self.root)}")
        return "\n".join(items) if items else "(empty)"
