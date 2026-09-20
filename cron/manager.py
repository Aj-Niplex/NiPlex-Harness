"""
# what this block
# Cron / scheduled jobs — storage.
# schedule examples: 'every 1h', 'every 30m', 'daily 09:00' (UTC).
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import cfg

JOBS_PATH = cfg.data_dir / "cron_jobs.json"


class CronManager:
    def __init__(self):
        self.jobs: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if JOBS_PATH.exists():
                self.jobs = json.loads(JOBS_PATH.read_text())
            else:
                self.jobs = []
        except Exception:
            self.jobs = []

    def _save(self):
        try:
            JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
            JOBS_PATH.write_text(json.dumps(self.jobs, indent=2))
        except Exception:
            pass

    def add_job(self, name: str, schedule: str, prompt: str, session_id: Optional[str] = None) -> str:
        job = {
            "id": str(int(time.time()))[-6:],
            "name": name,
            "schedule": schedule,
            "prompt": prompt,
            "session_id": session_id,
            "created": time.time(),
            "last_run": None,
            "enabled": True,
        }
        self.jobs.append(job)
        self._save()
        return f"Cron job added: {job['id']} ({name}) — {schedule}. Runs in this chat."

    def list_jobs(self) -> str:
        if not self.jobs:
            return "No cron jobs."
        lines = []
        for j in self.jobs:
            status = "ON" if j.get("enabled") else "OFF"
            last = "never" if not j.get("last_run") else time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(j["last_run"]))
            lines.append(f"{j['id']} [{status}] {j['name']} — {j['schedule']} (last ran: {last})")
        return "\n".join(lines)

    def remove_job(self, job_id: str) -> str:
        before = len(self.jobs)
        self.jobs = [j for j in self.jobs if j["id"] != job_id]
        self._save()
        if len(self.jobs) < before:
            return f"Removed job {job_id}"
        return f"Job {job_id} not found"
