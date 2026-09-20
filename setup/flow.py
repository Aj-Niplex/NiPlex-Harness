"""
# what this block
# Interactive setup state machine for /setup.
# why this code
# User only starts with bot token; /setup asks provider → key → models from API → save.
# optional if u want
# Add providers to PROVIDER_CHOICES + BASE_URLS as needed.
"""
from __future__ import annotations
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from config import ROOT

PROVIDER_CHOICES = [
    ("agnes", "Agnes"),
    ("google", "Google Gemini"),
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("openrouter", "OpenRouter"),
    ("custom", "Custom OpenAI-compatible"),
]

BASE_URLS = {
    "agnes": "https://apihub.agnes-ai.com/v1",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "anthropic": "https://api.anthropic.com/v1",
}

RUNTIME_ENV = ROOT / "data" / "runtime_provider.json"


@dataclass
class SetupSession:
    step: str = "provider"  # provider | api_key | base_url | model | done
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = field(default_factory=list)
    model: Optional[str] = None

    def choose_provider(self, key: str) -> str:
        key = key.lower().strip()
        valid = {k for k, _ in PROVIDER_CHOICES}
        if key not in valid:
            return "Unknown provider. Pick one of: " + ", ".join(valid)
        self.provider = key
        self.base_url = BASE_URLS.get(key)
        if key == "custom":
            self.step = "base_url"
            return "Send the base URL for your OpenAI-compatible API (example: https://api.example.com/v1)"
        if key == "google":
            self.step = "api_key"
            return "Send your **Google API key** (Gemini)."
        self.step = "api_key"
        return f"Send your **API key** for {key}."

    def set_base_url(self, url: str) -> str:
        self.base_url = url.strip().rstrip("/")
        self.step = "api_key"
        return "Send your **API key** for this custom endpoint."

    def set_api_key(self, key: str) -> str:
        self.api_key = key.strip()
        self.step = "fetch_models"
        return self.fetch_and_ask_models()

    def fetch_and_ask_models(self) -> str:
        models = list_models(self.provider or "", self.api_key or "", self.base_url)
        self.models = models
        self.step = "model"
        if not models:
            self.step = "model_manual"
            return (
                "Could not list models from the provider (key or network issue).\n"
                "Type a model id manually (example: gpt-4o-mini or gemini-2.0-flash)."
            )
        lines = ["**Available models** (from provider):"]
        for i, m in enumerate(models[:20], 1):
            lines.append(f"{i}. `{m}`")
        lines.append("\nReply with a number, a model id, or `random` to pick one.")
        return "\n".join(lines)

    def choose_model(self, text: str) -> str:
        text = text.strip()
        if text.lower() == "random" and self.models:
            self.model = random.choice(self.models[:20])
        elif text.isdigit() and self.models:
            idx = int(text) - 1
            if 0 <= idx < len(self.models[:20]):
                self.model = self.models[idx]
            else:
                return "Invalid number. Try again."
        else:
            self.model = text

        save_runtime_provider(
            provider=self.provider or "openai",
            api_key=self.api_key or "",
            base_url=self.base_url or "",
            model=self.model or "",
        )
        self.step = "done"
        return (
            f"Setup complete.\n"
            f"Provider: `{self.provider}`\n"
            f"Model: `{self.model}`\n"
            f"Saved to data/runtime_provider.json (not committed).\n"
            f"You can talk to **NiPlex Agent** now."
        )


def list_models(provider: str, api_key: str, base_url: Optional[str]) -> List[str]:
    try:
        if provider == "google":
            return _list_google(api_key)
        url = (base_url or BASE_URLS.get(provider) or "").rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/Aj-Niplex/NiPlex-Harness"
        with httpx.Client(timeout=25) as client:
            r = client.get(url, headers=headers)
            if r.status_code >= 300:
                return []
            data = r.json()
        items = data.get("data") or data.get("models") or []
        names = []
        for it in items:
            if isinstance(it, dict):
                mid = it.get("id") or it.get("name")
                if mid:
                    names.append(str(mid))
            elif isinstance(it, str):
                names.append(it)
        return names
    except Exception:
        return []


def _list_google(api_key: str) -> List[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        out = []
        for m in genai.list_models():
            name = getattr(m, "name", "") or ""
            if "/" in name:
                name = name.split("/", 1)[-1]
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods or not methods:
                if name:
                    out.append(name)
        return out
    except Exception:
        return ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]


def save_runtime_provider(provider: str, api_key: str, base_url: str, model: str) -> None:
    RUNTIME_ENV.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
    RUNTIME_ENV.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_runtime_provider() -> Optional[Dict[str, Any]]:
    if not RUNTIME_ENV.exists():
        return None
    try:
        return json.loads(RUNTIME_ENV.read_text(encoding="utf-8"))
    except Exception:
        return None
