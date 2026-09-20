"""Voice (TTS) tools. Optional — needs Piper."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


@tool({"type": "function", "function": {"name": "speak", "description": "Speak text as a voice message", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}})
def speak(agent: Any, args: Dict[str, Any]) -> str:
    try:
        import voice
        path, msg = voice.speak(args.get("text", ""), agent.session_id)
        if path:
            agent.outbound_files.append({"path": str(path), "filename": path.name})
        return msg
    except ImportError:
        return "Voice not available in this build. Enable the voice package and Piper."


@tool({"type": "function", "function": {"name": "set_voice", "description": "Pick Piper voice", "parameters": {"type": "object", "properties": {"voice": {"type": "string"}}, "required": ["voice"]}}})
def set_voice(agent: Any, args: Dict[str, Any]) -> str:
    try:
        import voice
        return voice.set_voice(args.get("voice", ""))
    except ImportError:
        return "Voice not available in this build."
