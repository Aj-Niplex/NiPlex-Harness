"""
Progress / status channel.

The AI can tell the harness what the user should see while it is working
(step-by-step reasoning visibility).
"""
from __future__ import annotations
from typing import List


class StatusChannel:
    def __init__(self):
        self.steps: List[str] = []

    def report(self, message: str) -> str:
        self.steps.append(message)
        return f"Status recorded: {message}"

    def get_progress(self) -> str:
        if not self.steps:
            return "No progress steps yet."
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.steps))

    def clear(self):
        self.steps.clear()
