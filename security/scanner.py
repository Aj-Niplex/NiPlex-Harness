"""
# what this block
# Risk scanner for terminal/code before it runs.
# why this code
# Hermes-style gates: free safe commands, HIGH/MEDIUM need approval, whitelist skips approval for exact matches.
# optional if u want
# Edit FREE_COMMAND_PATTERNS or rely on ApprovalStore.always_allow for user-chosen commands.
#
# SECURITY NOTE (fixed 2026-09-03): the free-command check must never run
# before the HIGH/MEDIUM scan, and must never be allowed to short-circuit
# on a single matching line of a multi-line payload. See scan_command().
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Set
import re

# Commands that never need approval (common & safe).
# These are meant to describe an ENTIRE trivial single-line statement,
# not just a prefix — is_free_command() enforces that.
FREE_COMMAND_PATTERNS = [
    r"^print\(",
    r"^len\(",
    r"^type\(",
    r"^help\(",
    r"^import\s+(math|json|re|datetime|pathlib|collections)\b",
    r"^from\s+(math|json|re|datetime|pathlib|collections)\s+import\b",
    r"^\s*#",  # comments only
    r"^pwd\s*$",
    r"^ls(\s|$)",
    r"^dir(\s|$)",
    r"^echo\s+",
    r"^whoami\s*$",
    r"^date\s*$",
    r"^cat\s+User Vault/",
    r"^cat\s+chances/",
    r"^head\s+",
    r"^tail\s+",
    r"^wc\s+",
    r"^python3?\s+-c\s+['\"]print\(",  # simple print one-liners
]

HIGH_PATTERNS = [
    (r"\brm\s+-r[f]?\b", "recursive delete"),
    (r"\brm\s+-fr\b", "recursive delete"),
    (r"\bshutil\.rmtree\b", "recursive delete"),
    (r"\bmkfs\b", "filesystem format"),
    (r"\bdd\s+if=", "raw disk write"),
    (r"\bchmod\s+-R\s+777\b", "world-writable recursive chmod"),
    (r"curl[^\n]*\|\s*(ba)?sh", "pipe remote script to shell"),
    (r"wget[^\n]*\|\s*(ba)?sh", "pipe remote script to shell"),
    (r"python3?\s+-c\s+", "inline interpreter with possible payload"),
    (r"subprocess\.(run|Popen|call)", "inline process spawn"),
    (r"os\.system\(", "os.system spawn"),
    (r"eval\(", "dynamic eval"),
    (r"exec\(", "dynamic exec"),
    (r"socket\.socket", "raw socket"),
    (r"/home/container/Voice", "protected Voice directory"),
]

MEDIUM_PATTERNS = [
    (r"\bgit\s+push\b", "git push"),
    (r"\bgit\s+reset\s+--hard\b", "destructive git reset"),
    (r"\bpip\s+install\b", "install packages"),
    (r"\bapt(-get)?\s+install\b", "system package install"),
    (r"\bchmod\b", "permission change"),
    (r"\bchown\b", "ownership change"),
    (r"open\([^)]*['\"]w", "file overwrite"),
]

PROTECTED_PATHS = [
    "/home/container/Voice",
    "agent/identity.py",
    "launch.py",
    ".env",
    "config.py",
]


@dataclass
class Risk:
    level: str  # FREE | LOW | MEDIUM | HIGH
    reasons: List[str]
    blocked: bool = False
    needs_approval: bool = False
    free: bool = False


def _normalize(cmd: str) -> str:
    return " ".join((cmd or "").strip().split())


def is_free_command(command: str) -> bool:
    """True only if the WHOLE command is one trivial free statement."""
    text = (command or "").strip()
    if not text or "\n" in text:
        return False
    for pat in FREE_COMMAND_PATTERNS:
        if re.search(pat, text, re.I):
            if re.search(r"\b(rm|unlink|rmtree)\b", text, re.I):
                return False
            return True
    return False


def scan_command(command: str, always_allow: Optional[Set[str]] = None) -> Risk:
    text = command or ""
    norm = _normalize(text)
    always_allow = always_allow or set()

    if norm in always_allow:
        return Risk(level="FREE", reasons=["always-allow whitelist"], needs_approval=False, free=True)

    reasons: List[str] = []
    level = "LOW"

    for path in PROTECTED_PATHS:
        if path.lower() in text.lower() and re.search(r"\b(rm|unlink|delete|rmtree)\b", text, re.I):
            reasons.append(f"protected path: {path}")
            level = "HIGH"

    for pat, why in HIGH_PATTERNS:
        if re.search(pat, text, re.I):
            reasons.append(why)
            level = "HIGH"

    if level != "HIGH":
        for pat, why in MEDIUM_PATTERNS:
            if re.search(pat, text, re.I):
                reasons.append(why)
                level = "MEDIUM"

    if level == "LOW" and is_free_command(text):
        return Risk(level="FREE", reasons=["common free command"], needs_approval=False, free=True)

    needs = level in ("MEDIUM", "HIGH")
    return Risk(level=level, reasons=reasons or ["no flagged patterns"], blocked=False, needs_approval=needs)
