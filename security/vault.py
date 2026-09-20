"""
# what this block
# Secret Vault: store secrets and substitute placeholders in code/commands.
# why this code
# User can store secrets (e.g., API keys) via a secure flow. The model references
# them via placeholders like {=SECRET_NAME=}. The harness substitutes the real
# value at execution time and redacts it from any output before it reaches
# the model's context, preventing secret leakage.
# optional if u want
# Secrets are stored in data/secrets_vault.json (gitignored).
#
# REDACTION IS BEST-EFFORT, NOT A HARD GUARANTEE: it only catches exact-value
# matches on the run_code output path. Treat this as raising the bar, not a seal.
"""
from __future__ import annotations
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List

from config import cfg

logger = logging.getLogger("niplex.security.vault")

VAULT_PATH = cfg.data_dir / "secrets_vault.json"
PLACEHOLDER_RE = re.compile(r"\{=([A-Za-z0-9_-]+)=\}")
SHORT_SECRET_THRESHOLD = 3


class SecretVault:
    """Store and manage secrets with placeholder substitution."""

    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        try:
            if VAULT_PATH.exists():
                data = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._secrets = data
        except Exception as e:
            logger.warning(f"Failed to load secrets vault: {e}")
            self._secrets = {}

    def _save(self) -> None:
        try:
            VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
            VAULT_PATH.write_text(
                json.dumps(self._secrets, indent=2),
                encoding="utf-8"
            )
            VAULT_PATH.chmod(0o600)
        except Exception as e:
            logger.warning(f"Failed to save secrets vault: {e}")

    def store_secret(self, name: str, value: str) -> str:
        name = name.strip()
        if not name:
            return "Secret name cannot be empty."
        if not re.match(r"^[A-Za-z0-9_-]+$", name):
            return "Secret name must contain only alphanumeric characters, hyphens, and underscores."
        if not value or not value.strip():
            return "Secret value cannot be empty."

        self._secrets[name] = value
        self._save()
        logger.info(f"Stored secret: {name}")
        return f"Secret '{name}' stored successfully."

    def remove_secret(self, name: str) -> str:
        name = name.strip()
        if name in self._secrets:
            del self._secrets[name]
            self._save()
            logger.info(f"Removed secret: {name}")
            return f"Secret '{name}' removed."
        return f"Secret '{name}' not found."

    def list_secrets(self) -> str:
        if not self._secrets:
            return "No secrets stored."
        return "Stored secrets: " + ", ".join(sorted(self._secrets.keys()))

    def get_secret(self, name: str) -> Optional[str]:
        return self._secrets.get(name.strip())

    def has_secret(self, name: str) -> bool:
        return name.strip() in self._secrets

    def substitute_placeholders(self, text: str) -> str:
        def replace(match):
            secret_name = match.group(1)
            secret_value = self.get_secret(secret_name)
            if secret_value is not None:
                return secret_value
            return match.group(0)

        return PLACEHOLDER_RE.sub(replace, text)

    def redact_secrets(self, text: str) -> str:
        if not self._secrets:
            return text

        result = text
        for name, value in self._secrets.items():
            if not value:
                continue
            escaped_value = re.escape(value)
            if len(value) <= SHORT_SECRET_THRESHOLD:
                logger.warning(
                    f"Secret '{name}' is <= {SHORT_SECRET_THRESHOLD} chars — "
                    "redacting as a whole-word match only, not a hard guarantee."
                )
                result = re.sub(rf"\b{escaped_value}\b", f"[REDACTED_{name}]", result)
            else:
                result = re.sub(escaped_value, f"[REDACTED_{name}]", result)
        return result

    def find_placeholders(self, text: str) -> List[str]:
        return PLACEHOLDER_RE.findall(text)


vault = SecretVault()


def get_vault() -> SecretVault:
    return vault


def substitute_in_text(text: str) -> str:
    return vault.substitute_placeholders(text)


def redact_from_text(text: str) -> str:
    return vault.redact_secrets(text)
