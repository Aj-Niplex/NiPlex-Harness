"""
Built-in Python workspace sandbox + external adapter.

Default (SANDBOX_MODE=builtin):
  - Sandboxed code runs in its OWN dedicated venv (data/sandbox_venv/)
  - Resource limits: memory, CPU, open files, max file size, process ceiling
  - Child process gets scrubbed env (no bot tokens / API keys)
  - Timeout kills the whole process group

External (SANDBOX_MODE=external):
  - POSTs code to SANDBOX_URL
"""
from __future__ import annotations
import ctypes
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import venv as _venv_module
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from config import cfg

_SECRET_ENV_PREFIXES = (
    "DISCORD_", "TELEGRAM_", "AGNES_", "OPENAI_", "GOOGLE_", "GITHUB_",
    "ANTHROPIC_", "OPENROUTER_", "HF_", "HUGGINGFACE_", "AWS_", "GROQ_",
    "XAI_", "DEEPSEEK_", "MISTRAL_", "TOGETHER_", "COHERE_", "AZURE_", "NTFY_",
)
_SECRET_ENV_EXACT = {
    "API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "AGNES_API_KEY",
    "GITHUB_PAT", "DISCORD_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "SANDBOX_API_KEY",
}

_PR_SET_NO_NEW_PRIVS = 38
SANDBOX_VENV_DIR = cfg.data_dir / "sandbox_venv"


def _scrubbed_env(python_bin: Optional[Path] = None) -> Dict[str, str]:
    keep = {"PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "TMPDIR", "TMP", "TEMP"}
    out: Dict[str, str] = {}
    for k, v in os.environ.items():
        ku = k.upper()
        if ku in _SECRET_ENV_EXACT:
            continue
        if any(ku.startswith(p) for p in _SECRET_ENV_PREFIXES):
            continue
        if "TOKEN" in ku or "SECRET" in ku or "PASSWORD" in ku or "API_KEY" in ku or "ACCESS_KEY" in ku:
            continue
        if k in keep or k.startswith("PYTHON"):
            out[k] = v
    out["PYTHONUNBUFFERED"] = "1"
    if python_bin is not None:
        venv_bin_dir = Path(python_bin).parent
        out["VIRTUAL_ENV"] = str(venv_bin_dir.parent)
        out["PATH"] = f"{venv_bin_dir}{os.pathsep}{out.get('PATH', '')}"
    return out


def _ensure_sandbox_venv() -> Optional[Path]:
    python_bin = SANDBOX_VENV_DIR / "bin" / "python"
    if python_bin.exists():
        return python_bin
    try:
        SANDBOX_VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        _venv_module.create(str(SANDBOX_VENV_DIR), with_pip=True, system_site_packages=False, clear=True)
        return python_bin if python_bin.exists() else None
    except Exception:
        return None


def reset_sandbox_venv() -> str:
    try:
        if SANDBOX_VENV_DIR.exists():
            shutil.rmtree(SANDBOX_VENV_DIR)
        return "Sandbox venv wiped. A fresh, empty one will be created on the next run_code call."
    except Exception as e:
        return f"Could not reset sandbox venv: {type(e).__name__}"


def _count_own_processes() -> Optional[int]:
    try:
        uid = os.getuid()
        count = 0
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                if os.stat(f"/proc/{entry}").st_uid == uid:
                    count += 1
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
        return count
    except Exception:
        return None


class BuiltinSandbox:
    NEW_PROCESS_BUDGET = 24
    MAX_OPEN_FILES = 256
    MAX_FILE_SIZE_MB = 200

    def __init__(self):
        self.timeout = cfg.sandbox_timeout
        self.max_mem = cfg.sandbox_max_memory_mb * 1024 * 1024

    def _preexec(self, nproc_ceiling: Optional[int]):
        max_mem = self.max_mem
        timeout = self.timeout
        max_open_files = self.MAX_OPEN_FILES
        max_file_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024

        def _apply():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
            except Exception:
                pass
            try:
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            except Exception:
                pass
            try:
                cpu_cap = timeout + 5
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_cap, cpu_cap))
            except Exception:
                pass
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (max_open_files, max_open_files))
            except Exception:
                pass
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_bytes, max_file_bytes))
            except Exception:
                pass
            if nproc_ceiling is not None:
                try:
                    resource.setrlimit(resource.RLIMIT_NPROC, (nproc_ceiling, nproc_ceiling))
                except Exception:
                    pass
            try:
                libc = ctypes.CDLL("libc.so.6", use_errno=True)
                libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
            except Exception:
                pass

        return _apply

    def run(self, code: str, language: str = "python") -> Dict[str, Any]:
        if language != "python":
            return {"error": "Built-in sandbox currently supports only Python. Use external for others."}

        python_bin = _ensure_sandbox_venv() or Path(sys.executable)

        with tempfile.TemporaryDirectory(prefix="niplex_ws_") as tmp:
            script = Path(tmp) / "main.py"
            script.write_text(code, encoding="utf-8")

            baseline = _count_own_processes() if os.name == "posix" else None
            nproc_ceiling = (baseline + self.NEW_PROCESS_BUDGET) if baseline is not None else None

            proc: Optional[subprocess.Popen] = None
            try:
                proc = subprocess.Popen(
                    [str(python_bin), str(script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=tmp,
                    env=_scrubbed_env(python_bin),
                    preexec_fn=self._preexec(nproc_ceiling) if os.name == "posix" else None,
                    start_new_session=True,
                )
                stdout, stderr = proc.communicate(timeout=self.timeout)
                return {
                    "stdout": (stdout or "")[:50_000],
                    "stderr": (stderr or "")[:50_000],
                    "exit_code": proc.returncode,
                    "timed_out": False,
                    "mode": "builtin",
                }
            except subprocess.TimeoutExpired:
                stdout, stderr = "", ""
                if proc is not None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    try:
                        stdout, stderr = proc.communicate(timeout=5)
                    except Exception:
                        pass
                return {
                    "stdout": (stdout or "")[:50_000],
                    "stderr": (stderr or "")[:50_000],
                    "exit_code": None,
                    "timed_out": True,
                    "mode": "builtin",
                }
            except Exception as e:
                if proc is not None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass
                return {"error": f"{type(e).__name__}: sandbox execution failed", "mode": "builtin"}


class ExternalSandbox:
    def __init__(self):
        if not cfg.sandbox_url:
            raise ValueError("SANDBOX_MODE=external requires SANDBOX_URL")
        self.url = cfg.sandbox_url.rstrip("/")
        self.api_key = cfg.sandbox_api_key

    def run(self, code: str, language: str = "python") -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"code": code, "language": language}
        try:
            with httpx.Client(timeout=cfg.sandbox_timeout + 10) as client:
                r = client.post(self.url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                data["mode"] = "external"
                return data
        except Exception as e:
            return {"error": str(e), "mode": "external"}


def get_sandbox():
    if cfg.sandbox_mode == "external":
        return ExternalSandbox()
    return BuiltinSandbox()
