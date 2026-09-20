"""
# what this block
# Pending approvals + Always-Allow exact-command whitelist + the /allow
# time-boxed full-access window.
# why this code
# User can Allow Once, Allow Session, or Always Allow *this exact command*
# only. Always-Allow is persisted under data/ so it survives process
# restarts. Pending approvals are also persisted per session.
#
# /allow is a time-boxed full-access window the user turns on deliberately.
"""
from __future__ import annotations
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from config import cfg

ALWAYS_ALLOW_PATH = cfg.data_dir / "always_allow.json"
PENDING_DIR = cfg.data_dir / "pending_approvals"

_SAFE_SESSION = re.compile(r"[^A-Za-z0-9_.-]+")


def _normalize(cmd: str) -> str:
    return " ".join((cmd or "").strip().split())


def _safe_session_filename(session_id: str) -> str:
    cleaned = _SAFE_SESSION.sub("_", session_id or "default").strip("._") or "default"
    return cleaned[:120]


def list_pending_sessions() -> List[str]:
    if not PENDING_DIR.exists():
        return []
    out: List[str] = []
    for f in PENDING_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                out.append(f.stem)
        except Exception:
            continue
    return out


@dataclass
class PendingApproval:
    id: str
    command: str
    reason: str
    level: str
    created: float = field(default_factory=time.time)


class ApprovalStore:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._pending_path = PENDING_DIR / f"{_safe_session_filename(session_id)}.json"
        self.pending: Dict[str, PendingApproval] = {}
        self.session_allow: bool = False
        self.always_allow: Set[str] = set()
        self.temp_allow_until: Optional[float] = None
        self._load_always_allow()
        self._load_pending()

    def _load_always_allow(self) -> None:
        try:
            if ALWAYS_ALLOW_PATH.exists():
                data = json.loads(ALWAYS_ALLOW_PATH.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.always_allow = {_normalize(x) for x in data if isinstance(x, str) and x.strip()}
        except Exception:
            self.always_allow = set()

    def _save_always_allow(self) -> None:
        try:
            ALWAYS_ALLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
            ALWAYS_ALLOW_PATH.write_text(
                json.dumps(sorted(self.always_allow), indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_pending(self) -> None:
        try:
            if self._pending_path.exists():
                data = json.loads(self._pending_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        try:
                            pa = PendingApproval(**item)
                            self.pending[pa.id] = pa
                        except Exception:
                            continue
        except Exception:
            self.pending = {}

    def _save_pending(self) -> None:
        try:
            self._pending_path.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(p) for p in self.pending.values()]
            self._pending_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def request(self, command: str, reason: str, level: str) -> PendingApproval:
        pid = str(uuid.uuid4())[:8]
        item = PendingApproval(id=pid, command=command, reason=reason, level=level)
        self.pending[pid] = item
        self._save_pending()
        return item

    def allow_once(self, pid: str) -> Optional[PendingApproval]:
        item = self.pending.pop(pid, None)
        if item is not None:
            self._save_pending()
        return item

    def deny(self, pid: str) -> bool:
        existed = self.pending.pop(pid, None) is not None
        if existed:
            self._save_pending()
        return existed

    def clear_pending(self) -> None:
        self.pending.clear()
        self._save_pending()

    def allow_session(self):
        self.session_allow = True

    def always_allow_command(self, command: str) -> str:
        norm = _normalize(command)
        if not norm:
            return "Empty command"
        self.always_allow.add(norm)
        self._save_always_allow()
        return (
            "Always allow registered for exact command (normalized). "
            "Only this exact text is free. Saved to data/always_allow.json."
        )

    def is_always_allowed(self, command: str) -> bool:
        return _normalize(command) in self.always_allow

    def start_temp_allow(self, minutes: float) -> str:
        self.temp_allow_until = time.time() + max(0.0, minutes) * 60
        mins = int(minutes) if float(minutes).is_integer() else minutes
        return f"Temporary full access is ON for {mins} minute(s) — every command runs without a prompt until then."

    def is_temp_allow_active(self) -> bool:
        return self.temp_allow_until is not None and time.time() < self.temp_allow_until

    def temp_allow_remaining_seconds(self) -> float:
        if not self.is_temp_allow_active():
            return 0.0
        return max(0.0, self.temp_allow_until - time.time())

    def cancel_temp_allow(self) -> str:
        had_active = self.is_temp_allow_active()
        self.temp_allow_until = None
        return "Temporary full access turned off." if had_active else "Temporary full access wasn't on."
