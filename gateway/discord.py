"""
Discord gateway: /setup, /help, /allow, approvals, chat, cron delivery.
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Dict

import discord
from discord.ext import commands

from agent import Agent
from config import cfg
from agent.identity import AGENT_FULL_NAME, HARNESS_NAME
from gateway.discord_ui import ApprovalView, AllowWindowView, approval_embed, allow_window_embed
from gateway.help_text import HELP_TEXT
from security.approvals import list_pending_sessions
from setup.flow import SetupSession, PROVIDER_CHOICES
from cron.scheduler import run_scheduler

logging.basicConfig(level=getattr(logging, cfg.log_level.upper(), logging.INFO))
logger = logging.getLogger("niplex.discord")

_agents: Dict[int, Agent] = {}
_setup: Dict[int, SetupSession] = {}
_scheduler_started = False
_startup_tasks_done = False


def _get_agent(channel_id: int) -> Agent:
    if channel_id not in _agents:
        _agents[channel_id] = Agent(session_id=f"dc_{channel_id}")
    return _agents[channel_id]


def _allowed(user_id: int) -> bool:
    if cfg.require_allowlist and not cfg.allowed_discord_ids:
        return False
    if not cfg.allowed_discord_ids:
        return False if cfg.require_allowlist else True
    return user_id in cfg.allowed_discord_ids


async def _send_outbound_files(message: discord.Message, agent: Agent):
    files = getattr(agent, "outbound_files", []) or []
    agent.outbound_files = []
    for item in files:
        path = Path(item.get("path", ""))
        name = item.get("filename") or path.name
        if not path.exists() or not path.is_file():
            await message.reply(f"Could not send file: {name}")
            continue
        try:
            await message.reply(file=discord.File(str(path), filename=name))
        except Exception:
            logger.exception("send file failed")
            await message.reply(f"Failed to send {name}")


async def _send_pending_approvals(message: discord.Message, agent: Agent):
    for item in list(agent.terminal.approvals.pending.values()):
        emb = approval_embed(item.id, item.level, item.reason, item.command)
        view = ApprovalView(agent, item.id, cfg.allowed_discord_ids, timeout=300)
        sent = await message.reply(embed=emb, view=view)
        view.message = sent


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)


class ProviderSelect(discord.ui.View):
    def __init__(self, user_id: int, session: SetupSession):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.session = session
        options = [discord.SelectOption(label=label, value=key) for key, label in PROVIDER_CHOICES]
        select = discord.ui.Select(placeholder="Choose AI provider", options=options)

        async def on_select(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("Not your setup.", ephemeral=True)
                return
            key = select.values[0]
            msg = self.session.choose_provider(key)
            await interaction.response.edit_message(content=msg, view=None)

        select.callback = on_select
        self.add_item(select)


async def _cron_send(session_id: str, text: str):
    if not session_id.startswith("dc_"):
        return
    try:
        channel_id = int(session_id[len("dc_"):])
    except ValueError:
        return
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            return
    for i in range(0, max(len(text), 1), 1900):
        chunk = text[i : i + 1900]
        if chunk:
            await channel.send(chunk)


@bot.event
async def on_ready():
    global _scheduler_started, _startup_tasks_done
    logger.info(f"Discord ready as {bot.user} ({AGENT_FULL_NAME} / {HARNESS_NAME})")
    if _startup_tasks_done:
        return
    _startup_tasks_done = True
    try:
        await bot.tree.sync()
    except Exception:
        logger.exception("app command tree sync failed (non-fatal)")
    await _repost_pending_approvals()
    if not _scheduler_started:
        _scheduler_started = True
        asyncio.create_task(run_scheduler(_cron_send))
        logger.info("cron scheduler task started")


async def _repost_pending_approvals():
    for session_id in list_pending_sessions():
        if not session_id.startswith("dc_"):
            continue
        try:
            channel_id = int(session_id[len("dc_"):])
        except ValueError:
            continue
        channel = bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(channel_id)
            except Exception:
                continue
        agent = _get_agent(channel_id)
        pending_items = list(agent.terminal.approvals.pending.values())
        if not pending_items:
            continue
        try:
            await channel.send("Restarted with approval(s) waiting. Use these buttons:")
        except Exception:
            continue
        for item in pending_items:
            emb = approval_embed(item.id, item.level, item.reason, item.command)
            view = ApprovalView(agent, item.id, cfg.allowed_discord_ids, timeout=300)
            try:
                sent = await channel.send(embed=emb, view=view)
                view.message = sent
            except Exception:
                pass


@bot.command(name="setup")
async def setup_cmd(ctx: commands.Context):
    if not _allowed(ctx.author.id):
        return
    session = SetupSession()
    _setup[ctx.author.id] = session
    text = f"**{HARNESS_NAME} setup** — {AGENT_FULL_NAME}\n\nStep 1/3 — Choose your AI **provider**:"
    await ctx.reply(text, view=ProviderSelect(ctx.author.id, session))


@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    if not _allowed(ctx.author.id):
        return
    await ctx.reply(HELP_TEXT[:1900])


@bot.command(name="reset")
async def reset_cmd(ctx: commands.Context):
    if not _allowed(ctx.author.id):
        return
    agent = Agent(session_id=f"dc_{ctx.channel.id}")
    agent.terminal.approvals.clear_pending()
    _agents[ctx.channel.id] = agent
    _setup.pop(ctx.author.id, None)
    await ctx.reply("Session reset.")


@bot.command(name="allow")
async def allow_cmd(ctx: commands.Context):
    if not _allowed(ctx.author.id):
        return
    agent = _get_agent(ctx.channel.id)
    if agent.terminal.approvals.is_temp_allow_active():
        remaining = int(agent.terminal.approvals.temp_allow_remaining_seconds())
        await ctx.reply(
            f"Temporary full access is already on ({remaining // 60}m {remaining % 60}s left).",
            embed=allow_window_embed(),
            view=AllowWindowView(agent, ctx.author.id, timeout=60),
        )
        return
    await ctx.reply(embed=allow_window_embed(), view=AllowWindowView(agent, ctx.author.id, timeout=60))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not _allowed(message.author.id):
        return

    session = _setup.get(message.author.id)
    content = message.content or ""
    if bot.user:
        content = content.replace(f"<@{bot.user.id}>", "").strip()

    if session and session.step != "done" and not content.startswith("/"):
        reply = None
        if session.step == "base_url":
            reply = session.set_base_url(content)
        elif session.step == "api_key":
            try:
                await message.delete()
            except Exception:
                pass
            reply = session.set_api_key(content)
        elif session.step in ("model", "model_manual"):
            reply = session.choose_model(content)
            if session.step == "done":
                _setup.pop(message.author.id, None)
        if reply:
            await message.channel.send(reply[:1900])
            await bot.process_commands(message)
            return

    if message.guild and bot.user not in message.mentions:
        await bot.process_commands(message)
        return
    if not content or content.startswith("/"):
        await bot.process_commands(message)
        return

    agent = None
    async with message.channel.typing():
        try:
            agent = _get_agent(message.channel.id)
            reply = agent.chat(content, platform_username=message.author.name)
        except ValueError as e:
            reply = f"{e}\nRun `/setup` to configure provider + key + model."
        except Exception as e:
            logger.exception("Agent error")
            reply = f"Error: {type(e).__name__}"

    clean = reply
    if "Command Approval Required" in (reply or ""):
        clean = f"{AGENT_FULL_NAME}: a command needs your approval.\nUse the buttons below."
    for i in range(0, max(len(clean), 1), 1900):
        chunk = clean[i : i + 1900]
        if chunk:
            await message.reply(chunk)

    if agent is not None:
        await _send_pending_approvals(message, agent)
        await _send_outbound_files(message, agent)
    await bot.process_commands(message)


def run():
    if not cfg.discord_token:
        raise SystemExit("DISCORD_BOT_TOKEN is required when GATEWAY=discord")
    if cfg.require_allowlist and not cfg.allowed_discord_ids:
        raise SystemExit("ALLOWED_DISCORD_IDS is required (REQUIRE_ALLOWLIST=true)")
    logger.info(f"Discord gateway starting ({AGENT_FULL_NAME} / {HARNESS_NAME})...")
    bot.run(cfg.discord_token)
