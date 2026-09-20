"""
Cron scheduler — runs due jobs and delivers results via send_fn.
Minimal public version; full logic matches private harness behavior.
"""
from __future__ import annotations
import asyncio
import logging
import time
from typing import Awaitable, Callable

from cron.manager import CronManager

logger = logging.getLogger("niplex.cron")

SendFn = Callable[[str, str], Awaitable[None]]


def _is_due(job: dict, now: float) -> bool:
    schedule = (job.get("schedule") or "").strip().lower()
    last = job.get("last_run")
    if not job.get("enabled", True):
        return False
    if schedule.startswith("every "):
        part = schedule[6:].strip()
        try:
            if part.endswith("h"):
                secs = float(part[:-1]) * 3600
            elif part.endswith("m"):
                secs = float(part[:-1]) * 60
            else:
                return False
        except ValueError:
            return False
        if last is None:
            return True
        return (now - float(last)) >= secs
    # daily HH:MM not fully implemented in minimal public stub
    return False


async def run_scheduler(send_fn: SendFn, poll_seconds: float = 30.0):
    """Background loop: check jobs, run due ones with restricted tools."""
    from agent import Agent

    mgr = CronManager()
    while True:
        try:
            mgr._load()
            now = time.time()
            for job in list(mgr.jobs):
                if not _is_due(job, now):
                    continue
                session_id = job.get("session_id") or "default"
                prompt = job.get("prompt") or ""
                name = job.get("name") or job.get("id")
                logger.info(f"cron: running job {job.get('id')} ({name})")
                try:
                    agent = Agent(session_id=session_id)
                    # Restricted tool set for unattended runs — no terminal/code
                    safe = [t for t in agent._active_tools() if t["function"]["name"] not in (
                        "run_code", "start_new_terminal", "reset_sandbox_venv"
                    )]
                    result = agent.chat(prompt, tools_override=safe)
                    await send_fn(session_id, f"[cron:{name}]\n{result}")
                except Exception:
                    logger.exception(f"cron job {job.get('id')} failed")
                job["last_run"] = now
                mgr._save()
        except Exception:
            logger.exception("cron scheduler loop error")
        await asyncio.sleep(poll_seconds)
