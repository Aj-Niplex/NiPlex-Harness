"""
# what this block
# Loads env into a single Config object.
# why this code
# One place for tokens, allowlists, sandbox, and opt-in GitHub issues.
# optional if u want
# Prefer .env; use /setup for provider keys.
"""
from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent


@dataclass
class Config:
    gateway: str = os.getenv("GATEWAY", "discord").lower()
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    memory_root: Path = Path(os.getenv("MEMORY_ROOT", "./data")).resolve()

    provider: str = os.getenv("PROVIDER", "agnes").lower()
    agnes_api_key: Optional[str] = os.getenv("AGNES_API_KEY")
    agnes_base_url: str = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
    agnes_model: str = os.getenv("AGNES_MODEL", "agnes-2.0-flash")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    google_model: str = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    telegram_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    allowed_telegram_ids: List[int] = field(default_factory=list)
    discord_token: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")
    allowed_discord_ids: List[int] = field(default_factory=list)
    require_allowlist: bool = os.getenv("REQUIRE_ALLOWLIST", "true").lower() in ("1", "true", "yes")

    sandbox_mode: str = os.getenv("SANDBOX_MODE", "builtin").lower()
    sandbox_timeout: int = int(os.getenv("SANDBOX_TIMEOUT", "60"))
    sandbox_max_memory_mb: int = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))
    sandbox_url: Optional[str] = os.getenv("SANDBOX_URL")
    sandbox_api_key: Optional[str] = os.getenv("SANDBOX_API_KEY")
    auto_approve_low: bool = os.getenv("AUTO_APPROVE_LOW", "true").lower() in ("1", "true", "yes")

    enable_github_issues: bool = os.getenv("ENABLE_GITHUB_ISSUES", "false").lower() in ("1", "true", "yes")
    github_pat: Optional[str] = os.getenv("GITHUB_PAT")
    github_issues_repo: str = os.getenv("GITHUB_ISSUES_REPO", "Aj-Niplex/NiPlex-Harness")

    ntfy_topic: Optional[str] = os.getenv("NTFY_TOPIC")
    ntfy_url: str = os.getenv("NTFY_URL", "https://ntfy.sh")

    mcp_connectors: List[str] = field(default_factory=list)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        tg = os.getenv("ALLOWED_TELEGRAM_IDS", "")
        if tg.strip():
            self.allowed_telegram_ids = [int(x.strip()) for x in tg.split(",") if x.strip()]
        dc = os.getenv("ALLOWED_DISCORD_IDS", "")
        if dc.strip():
            self.allowed_discord_ids = [int(x.strip()) for x in dc.split(",") if x.strip()]
        raw = os.getenv("MCP_CONNECTORS", "")
        if raw.strip():
            self.mcp_connectors = [u.strip() for u in raw.split(",") if u.strip()]

        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_root / "global").mkdir(parents=True, exist_ok=True)
        (self.memory_root / "sessions").mkdir(parents=True, exist_ok=True)
        (ROOT / "vault").mkdir(exist_ok=True)


cfg = Config()
