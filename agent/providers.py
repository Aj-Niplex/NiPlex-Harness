"""
# what this block
# Model providers + runtime overrides from /setup.
# why this code
# Supports Agnes, Google, OpenAI, Anthropic (via OpenAI-compatible proxy), OpenRouter, custom.
# optional if u want
# Runtime keys live in data/runtime_provider.json after /setup (not in git).
"""
from __future__ import annotations
import json
import math
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import cfg
from setup.flow import load_runtime_provider


class BaseProvider:
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        result: Dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        return result


_GEMINI_SCHEMA_ALLOWED_KEYS = {"type", "description", "properties", "enum", "required", "items"}


def _sanitize_gemini_schema(schema: Any) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return {}
    cleaned: Dict[str, Any] = {}
    for key, value in schema.items():
        if key not in _GEMINI_SCHEMA_ALLOWED_KEYS:
            continue
        if key == "properties" and isinstance(value, dict):
            cleaned[key] = {
                pname: _sanitize_gemini_schema(pschema)
                for pname, pschema in value.items()
                if isinstance(pname, str)
            }
            continue
        if key == "items":
            cleaned[key] = _sanitize_gemini_schema(value)
            continue
        cleaned[key] = value

    enum_val = cleaned.get("enum")
    type_val = cleaned.get("type")
    if isinstance(enum_val, list) and type_val in {"integer", "number", "boolean"}:
        out = []
        for item in enum_val:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, bool):
                out.append("true" if item else "false")
            elif isinstance(item, (int, float)) and math.isfinite(item):
                out.append(str(item))
        if out:
            cleaned["enum"] = out
        else:
            cleaned.pop("enum", None)

    required_val = cleaned.get("required")
    if isinstance(required_val, list):
        prop_names = set(cleaned.get("properties", {}).keys())
        valid = [n for n in required_val if isinstance(n, str) and n in prop_names]
        if valid:
            cleaned["required"] = valid
        else:
            cleaned.pop("required", None)

    return cleaned


class GoogleProvider(BaseProvider):
    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model_name = model

    @staticmethod
    def _convert_tools(tools: Optional[List[Dict]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        decls = []
        for t in tools:
            fn = t.get("function", {})
            if not fn.get("name"):
                continue
            params = _sanitize_gemini_schema(fn.get("parameters") or {})
            if not params:
                params = {"type": "object", "properties": {}}
            decls.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "parameters": params,
            })
        return [{"function_declarations": decls}] if decls else None

    @staticmethod
    def _build_history(messages: List[Dict[str, Any]]):
        system_parts: List[str] = []
        history: List[Dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "system":
                system_parts.append(m.get("content") or "")
            elif role == "user":
                history.append({"role": "user", "parts": [{"text": m.get("content") or ""}]})
            elif role == "assistant":
                tool_calls = m.get("tool_calls")
                if tool_calls:
                    parts = []
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            args = {}
                        parts.append({"function_call": {"name": fn.get("name"), "args": args}})
                    history.append({"role": "model", "parts": parts})
                else:
                    history.append({"role": "model", "parts": [{"text": m.get("content") or ""}]})
            elif role == "tool":
                name = m.get("tool_call_id") or "tool"
                history.append({
                    "role": "function",
                    "parts": [{"function_response": {"name": name, "response": {"result": m.get("content") or ""}}}],
                })
        system = "\n".join(p for p in system_parts if p).strip()
        return system, history

    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        system, history = self._build_history(messages)
        gemini_tools = self._convert_tools(tools)
        try:
            model = self._genai.GenerativeModel(
                self.model_name,
                system_instruction=system or None,
                tools=gemini_tools,
            )
            resp = model.generate_content(history)
            candidate = resp.candidates[0] if getattr(resp, "candidates", None) else None
            parts = candidate.content.parts if candidate and candidate.content else []

            text_out: List[str] = []
            tool_calls_out: List[Dict[str, Any]] = []
            for part in parts:
                fc = getattr(part, "function_call", None)
                if fc is not None and getattr(fc, "name", None):
                    args = dict(fc.args) if getattr(fc, "args", None) else {}
                    tool_calls_out.append({
                        "id": fc.name,
                        "type": "function",
                        "function": {"name": fc.name, "arguments": json.dumps(args)},
                    })
                else:
                    t = getattr(part, "text", None)
                    if t:
                        text_out.append(t)

            result: Dict[str, Any] = {"role": "assistant", "content": "\n".join(text_out)}
            if tool_calls_out:
                result["tool_calls"] = tool_calls_out
            return result
        except Exception as e:
            return {"role": "assistant", "content": f"Google provider error: {type(e).__name__}: {e}"}


def get_provider() -> BaseProvider:
    runtime = load_runtime_provider() or {}
    provider = (runtime.get("provider") or cfg.provider or "agnes").lower()
    api_key = runtime.get("api_key") or ""
    base_url = runtime.get("base_url") or ""
    model = runtime.get("model") or ""

    if provider == "agnes":
        key = api_key or cfg.agnes_api_key
        if not key:
            raise ValueError("No Agnes key. Run /setup")
        return OpenAICompatibleProvider(
            key,
            base_url or cfg.agnes_base_url,
            model or cfg.agnes_model,
        )
    if provider == "google":
        key = api_key or cfg.google_api_key
        if not key:
            raise ValueError("No Google key. Run /setup")
        return GoogleProvider(key, model or cfg.google_model)
    if provider in ("openai", "openrouter", "custom", "anthropic"):
        key = api_key or cfg.openai_api_key
        if not key:
            raise ValueError("No API key. Run /setup")
        url = base_url or cfg.openai_base_url
        if provider == "openrouter" and not base_url:
            url = "https://openrouter.ai/api/v1"
        if provider == "anthropic":
            if not base_url:
                raise ValueError(
                    "Anthropic needs an OpenAI-compatible proxy URL. "
                    "Use /setup → Custom and set a proxy base URL, or use OpenRouter."
                )
            url = base_url
        return OpenAICompatibleProvider(key, url, model or cfg.openai_model)

    raise ValueError(f"Unknown provider={provider}. Run /setup")
