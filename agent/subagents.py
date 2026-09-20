"""
Simple sub-agent spawning (Hermes-inspired delegation).

On free tier we keep sub-agents lightweight: they share the same provider
but get isolated short history + optional restricted tools.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid


class SubAgent:
    def __init__(self, name: str, goal: str, parent_session: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.goal = goal
        self.parent_session = parent_session
        self.history: List[Dict[str, Any]] = []
        self.done = False
        self.result: Optional[str] = None

    def summary(self) -> str:
        return f"[{self.id}] {self.name} — goal: {self.goal} — done={self.done}"


class SubAgentManager:
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}

    def spawn(self, name: str, goal: str, parent_session: str = "default") -> str:
        sa = SubAgent(name=name, goal=goal, parent_session=parent_session)
        self.agents[sa.id] = sa
        return f"Spawned sub-agent {sa.id} ({name}) for goal: {goal}"

    def list_subagents(self) -> str:
        if not self.agents:
            return "No sub-agents."
        return "\n".join(a.summary() for a in self.agents.values())

    def report_result(self, sub_id: str, result: str) -> str:
        sa = self.agents.get(sub_id)
        if not sa:
            return f"Sub-agent {sub_id} not found"
        sa.result = result
        sa.done = True
        return f"Sub-agent {sub_id} marked done."

    def get_result(self, sub_id: str) -> str:
        sa = self.agents.get(sub_id)
        if not sa:
            return f"Sub-agent {sub_id} not found"
        return sa.result or "(still working)"
