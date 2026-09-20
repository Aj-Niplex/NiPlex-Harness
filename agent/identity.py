"""
# what this block
# Agent identity/branding. Structural product names stay as constants;
# persona/attribution details live in data/soul.md so they're editable
# without a code deploy — by you directly, or by the agent via its own
# file tools.
# why this code
# Complaint from live use: hardcoding creator facts in the system prompt
# got read by the model as a fact about whoever is chatting. soul.md fixes
# the root cause (editable, separates attribution from identity).
# optional if u want
# HARNESS_NAME/AGENT_NAME stay real constants — gateway files import these
# for UI strings. Only the persona/attribution block is soul.md-driven.
"""
from __future__ import annotations
from pathlib import Path

from config import cfg

HARNESS_NAME = "NiPlex Harness"
AGENT_NAME = "NiPlex"
AGENT_FULL_NAME = "NiPlex"

SOUL_PATH = cfg.data_dir / "soul.md"

DEFAULT_SOUL = """# Soul

Edit this file directly, or ask the agent to update it (it can write here
with its own file tools) — changes take effect on your very next message,
no restart needed.

## Agent
- Name: NiPlex
- Signature: — NiPlex · NiPlex Harness

## Attribution (branding, not identity — see notes below)
- Powered by: NiPlex Harness
- Developed by: Aj-Niplex (Adarsh Jaiswal)
- Organization: Niplex

## Notes for the agent reading this file
- Everything above is branding for the software itself — who built and owns
  this deployment. It is NOT a fact about who is currently chatting with you.
- Never assert the current user's name from this file. Their name, if you
  know it at all, comes from the actual conversation, from the platform
  username you're given each message, or from memory — never from this
  attribution section.
- If asked who they are and nothing in this conversation or in memory
  actually says so, say you don't know rather than guessing.
"""


def _ensure_soul_file() -> Path:
    try:
        SOUL_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not SOUL_PATH.exists():
            SOUL_PATH.write_text(DEFAULT_SOUL, encoding="utf-8")
    except Exception:
        pass  # never crash the agent on disk issues
    return SOUL_PATH


def get_soul_text() -> str:
    """Read soul.md fresh every call — no caching — so an edit made by the
    user or by the agent itself is picked up on the very next message."""
    path = _ensure_soul_file()
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return DEFAULT_SOUL


def get_identity_block() -> str:
    return f"""You are running on {HARNESS_NAME}.
You never pretend to be Claude, GPT, Gemini, Hermes, or any other product.

{get_soul_text()}
"""


def get_signature() -> str:
    """Pull the 'Signature:' line out of soul.md; falls back to a sane
    default if it's missing (e.g. the user deleted that line)."""
    for line in get_soul_text().splitlines():
        line = line.strip()
        if line.lower().startswith("- signature:"):
            return line.split(":", 1)[1].strip()
    return f"— {AGENT_NAME} · {HARNESS_NAME}"


def get_creator_handle() -> str:
    """Pull the 'Developed by:' line out of soul.md."""
    for line in get_soul_text().splitlines():
        line = line.strip()
        if line.lower().startswith("- developed by:"):
            return line.split(":", 1)[1].strip()
    return "Aj-Niplex"
