"""
Discord embed + buttons for command approval and /allow window.
"""
from __future__ import annotations
import discord
from discord.ui import View, button
from typing import TYPE_CHECKING, Optional

from agent.identity import AGENT_FULL_NAME, HARNESS_NAME

if TYPE_CHECKING:
    from agent import Agent


def _footer() -> str:
    return f"{AGENT_FULL_NAME} · {HARNESS_NAME}"


def approval_embed(approval_id: str, level: str, reason: str, command: str) -> discord.Embed:
    color = discord.Color.red() if level == "HIGH" else discord.Color.orange()
    emb = discord.Embed(
        title="Command Approval Required",
        description=(
            f"**Level:** `{level}`\n"
            f"**Reason:** {reason}\n"
            f"**Id:** `{approval_id}`\n\n"
            f"```\n{command[:900]}\n```\n\n"
            f"**Always Allow** only unlocks this exact command text."
        ),
        color=color,
    )
    emb.set_footer(text=_footer())
    return emb


def allow_window_embed() -> discord.Embed:
    emb = discord.Embed(
        title="Temporary full access",
        description=(
            "Pick how long every command should run **without an approval prompt**. "
            "Self-expiring. Separate from Always Allow (one exact command forever)."
        ),
        color=discord.Color.gold(),
    )
    emb.set_footer(text=_footer())
    return emb


class ApprovalView(View):
    def __init__(self, agent: "Agent", approval_id: str, allowed_ids: list, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.agent = agent
        self.approval_id = approval_id
        self.allowed_ids = set(allowed_ids or [])
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.allowed_ids and interaction.user.id not in self.allowed_ids:
            await interaction.response.send_message("You are not allowed to approve this.", ephemeral=True)
            return False
        return True

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    async def on_timeout(self):
        self._disable_all()
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @button(label="Allow Once", style=discord.ButtonStyle.success)
    async def allow_once(self, interaction: discord.Interaction, btn: discord.ui.Button):
        result = self.agent.terminal.approve_and_run(self.approval_id)
        self._disable_all()
        emb = discord.Embed(title="Allowed once", description=f"```\n{result[:1500]}\n```", color=discord.Color.green())
        emb.set_footer(text=_footer())
        await interaction.response.edit_message(embed=emb, view=self)

    @button(label="Allow Session", style=discord.ButtonStyle.primary)
    async def allow_session(self, interaction: discord.Interaction, btn: discord.ui.Button):
        self.agent.terminal.approvals.allow_session()
        result = self.agent.terminal.approve_and_run(self.approval_id)
        self._disable_all()
        emb = discord.Embed(
            title="Allowed for this session",
            description=f"Medium/high auto-run until reset.\n```\n{result[:1200]}\n```",
            color=discord.Color.blue(),
        )
        emb.set_footer(text=_footer())
        await interaction.response.edit_message(embed=emb, view=self)

    @button(label="Always Allow", style=discord.ButtonStyle.secondary)
    async def always_allow(self, interaction: discord.Interaction, btn: discord.ui.Button):
        result = self.agent.terminal.always_allow_and_run(self.approval_id)
        self._disable_all()
        emb = discord.Embed(
            title="Always Allow (exact command only)",
            description=f"```\n{result[:1500]}\n```",
            color=discord.Color.teal(),
        )
        emb.set_footer(text="Only this exact command is free next time")
        await interaction.response.edit_message(embed=emb, view=self)

    @button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, btn: discord.ui.Button):
        msg = self.agent.terminal.deny(self.approval_id)
        self._disable_all()
        emb = discord.Embed(title="Denied", description=msg, color=discord.Color.dark_grey())
        await interaction.response.edit_message(embed=emb, view=self)


class AllowWindowView(View):
    def __init__(self, agent: "Agent", user_id: int, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.agent = agent
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your /allow prompt.", ephemeral=True)
            return False
        return True

    async def _start(self, interaction: discord.Interaction, minutes: int):
        msg = self.agent.terminal.approvals.start_temp_allow(minutes)
        self._disable_all()
        emb = discord.Embed(title="Temporary full access is ON", description=msg, color=discord.Color.gold())
        emb.set_footer(text=_footer())
        await interaction.response.edit_message(embed=emb, view=self)

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    @button(label="5 min", style=discord.ButtonStyle.secondary)
    async def five(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self._start(interaction, 5)

    @button(label="10 min", style=discord.ButtonStyle.secondary)
    async def ten(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self._start(interaction, 10)

    @button(label="30 min", style=discord.ButtonStyle.primary)
    async def thirty(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self._start(interaction, 30)

    @button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, btn: discord.ui.Button):
        self._disable_all()
        await interaction.response.edit_message(content="Cancelled — no change.", embed=None, view=self)
