"""
# what this block
# Terminal sessions + approval-aware run_code.
# why this code
# FREE / always-allow commands run immediately; others wait for embed buttons.
"""
from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sandbox import get_sandbox, reset_sandbox_venv, BuiltinSandbox
from security.scanner import scan_command
from security.approvals import ApprovalStore


@dataclass
class TerminalSession:
    id: str
    name: str
    created_at: float
    last_used: float
    history: List[Dict[str, Any]] = field(default_factory=list)
    alive: bool = True
    max_history: int = 20


class TerminalManager:
    def __init__(self, session_id: str = "default"):
        self.sessions: Dict[str, TerminalSession] = {}
        self.sandbox = get_sandbox()
        self.approvals = ApprovalStore(session_id=session_id)

    def start_new_terminal(self, name: str = "main") -> str:
        tid = str(uuid.uuid4())[:8]
        now = time.time()
        self.sessions[tid] = TerminalSession(id=tid, name=name, created_at=now, last_used=now)
        return f"Started terminal '{name}' id={tid}"

    def list_terminals(self) -> str:
        if not self.sessions:
            return "No active terminals."
        return "\n".join(
            f"{s.id} name={s.name} status={'alive' if s.alive else 'dead'} cmds={len(s.history)}"
            for s in self.sessions.values()
        )

    def _ensure(self, terminal_id: Optional[str]) -> Optional[TerminalSession]:
        if not terminal_id:
            if not self.sessions:
                self.start_new_terminal("default")
            terminal_id = next(iter(self.sessions))
        return self.sessions.get(terminal_id)

    def run_code(self, code: str, terminal_id: Optional[str] = None, approved: bool = False) -> str:
        sess = self._ensure(terminal_id)
        if not sess or not sess.alive:
            return "Terminal not found or dead."

        risk = scan_command(code, always_allow=self.approvals.always_allow)
        if risk.free or risk.level == "FREE":
            approved = True

        if (
            risk.needs_approval
            and not approved
            and not self.approvals.session_allow
            and not self.approvals.is_temp_allow_active()
        ):
            item = self.approvals.request(code, "; ".join(risk.reasons), risk.level)
            return (
                f"Command Approval Required\n"
                f"id: {item.id}\n"
                f"level: {risk.level}\n"
                f"reason: {item.reason}\n"
                f"No action taken yet. Waiting for user button approval."
            )

        from security.vault import get_vault
        vault = get_vault()
        substituted_code = vault.substitute_placeholders(code)

        result = self.sandbox.run(substituted_code, language="python")

        if isinstance(result, dict):
            for key, value in list(result.items()):
                if isinstance(value, str):
                    result[key] = vault.redact_secrets(value)

        sess.last_used = time.time()
        sess.history.append({"code": code[:500], "result": result, "ts": sess.last_used})
        if len(sess.history) > sess.max_history:
            sess.history = sess.history[-sess.max_history :]
        return json.dumps({"terminal_id": sess.id, **result}, ensure_ascii=False)

    def approve_and_run(self, approval_id: str) -> str:
        item = self.approvals.allow_once(approval_id)
        if not item:
            return f"No pending approval {approval_id}"
        return self.run_code(item.command, approved=True)

    def always_allow_and_run(self, approval_id: str) -> str:
        item = self.approvals.allow_once(approval_id)
        if not item:
            return f"No pending approval {approval_id}"
        note = self.approvals.always_allow_command(item.command)
        result = self.run_code(item.command, approved=True)
        return f"{note}\n{result}"

    def deny(self, approval_id: str) -> str:
        ok = self.approvals.deny(approval_id)
        return f"Denied {approval_id}" if ok else f"No pending approval {approval_id}"

    def reset_sandbox(self) -> str:
        if not isinstance(self.sandbox, BuiltinSandbox):
            return "Sandbox venv reset only applies to SANDBOX_MODE=builtin."
        return reset_sandbox_venv()

    def get_results(self, terminal_id: str, last_n: int = 5) -> str:
        sess = self.sessions.get(terminal_id)
        if not sess:
            return f"Terminal {terminal_id} not found"
        return json.dumps(sess.history[-last_n:], ensure_ascii=False, indent=2)

    def set_terminal_lifecycle(self, terminal_id: str, action: str) -> str:
        sess = self.sessions.get(terminal_id)
        if not sess:
            return f"Terminal {terminal_id} not found"
        if action == "kill":
            sess.alive = False
            return f"Terminal {terminal_id} killed"
        if action == "keep_alive":
            sess.last_used = time.time()
            sess.alive = True
            return f"Terminal {terminal_id} kept alive"
        if action == "reset_history":
            sess.history.clear()
            return f"History cleared for {terminal_id}"
        return f"Unknown action {action}"
