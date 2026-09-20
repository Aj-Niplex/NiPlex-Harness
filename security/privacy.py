"""
NiPlex Harness — strip tokens, keys, paths that look private before any outbound report.
"""
from __future__ import annotations
import re

_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|authorization|bearer)\s*[=:]\s*['\"]?[^\s'\"]+", re.I), r"\1=[REDACTED]"),
    (re.compile(r"ghp_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_PAT]"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_PAT]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "[REDACTED_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z_-]{20,}"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"[0-9]{8,12}:[A-Za-z0-9_-]{30,}"), "[REDACTED_TELEGRAM_TOKEN]"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]+"), "Bearer [REDACTED]"),
    (re.compile(r"[MNOD][A-Za-z0-9_-]{23,}\.[A-Za-z0-9_-]{6,}"), "[REDACTED_DISCORD_TOKEN]"),
    (re.compile(r"ntfy_[A-Za-z0-9_-]{20,}"), "[REDACTED_NTFY_TOPIC]"),
    (re.compile(r"(?i)(GITHUB_PAT|DISCORD_TOKEN|TELEGRAM_TOKEN|NTFY_TOPIC|API_KEY|SECRET_KEY)\s*[=:]\s*['\"]?[^\s'\"]+['\"]?", re.I), r"\1=[REDACTED]"),
]


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out[:8000]
