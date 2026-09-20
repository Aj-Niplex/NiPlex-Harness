"""
Telegram gateway: /setup, /help, /allow, approvals, chat, cron delivery.
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent import Agent
from config import cfg
from agent.identity import AGENT_FULL_NAME, HARNESS_NAME
from gateway.help_text import HELP_TEXT
from setup.flow import SetupSession, PROVIDER_CHOICES
from cron.scheduler import run_scheduler

logging.basicConfig(level=getattr(logging, cfg.log_level.upper(), logging.INFO))
logger = logging.getLogger("niplex.tg")

_agents: Dict[int, Agent] = {}
_setup: Dict[int, SetupSession] = {}


def _get_agent(chat_id: int) -> Agent:
    if chat_id not in _agents:
        _agents[chat_id] = Agent(session_id=f"tg_{chat_id}")
    return _agents[chat_id]


def _allowed(user_id: int) -> bool:
    if cfg.require_allowlist and not cfg.allowed_telegram_ids:
        return False
    if not cfg.allowed_telegram_ids:
        return False if cfg.require_allowlist else True
    return user_id in cfg.allowed_telegram_ids


def _approval_keyboard(approval_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Allow Once", callback_data=f"allow:{approval_id}"),
            InlineKeyboardButton("Allow Session", callback_data=f"session:{approval_id}"),
        ],
        [
            InlineKeyboardButton("Always Allow", callback_data=f"always:{approval_id}"),
            InlineKeyboardButton("Deny", callback_data=f"deny:{approval_id}"),
        ],
    ])


def _provider_keyboard() -> InlineKeyboardMarkup:
    rows, row = [], []
    for key, label in PROVIDER_CHOICES:
        row.append(InlineKeyboardButton(label, callback_data=f"prov:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _allow_window_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("5 min", callback_data="allowwin:5"),
            InlineKeyboardButton("10 min", callback_data="allowwin:10"),
            InlineKeyboardButton("30 min", callback_data="allowwin:30"),
        ],
        [InlineKeyboardButton("Cancel", callback_data="allowwin:cancel")],
    ])


async def _send_outbound_files(update: Update, agent: Agent):
    files = getattr(agent, "outbound_files", []) or []
    agent.outbound_files = []
    for item in files:
        path = Path(item.get("path", ""))
        name = item.get("filename") or path.name
        if not path.exists() or not path.is_file():
            await update.message.reply_text(f"Could not send file: {name}")
            continue
        try:
            with path.open("rb") as fh:
                await update.message.reply_document(document=fh, filename=name)
        except Exception:
            logger.exception("send file failed")
            await update.message.reply_text(f"Failed to send {name}")


async def _send_pending_approvals(update: Update, agent: Agent):
    for item in list(agent.terminal.approvals.pending.values()):
        text = (
            f"Command Approval Required\n"
            f"Level: {item.level}\nReason: {item.reason}\nId: {item.id}\n\n"
            f"{item.command[:800]}\n\n{AGENT_FULL_NAME} · {HARNESS_NAME}"
        )
        await update.message.reply_text(text, reply_markup=_approval_keyboard(item.id))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not _allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        f"{AGENT_FULL_NAME} on {HARNESS_NAME}.\nRun /setup then /help."
    )


async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not _allowed(update.effective_user.id):
        return
    session = SetupSession()
    _setup[update.effective_user.id] = session
    await update.message.reply_text(
        f"{HARNESS_NAME} setup — Step 1/3: choose provider",
        reply_markup=_provider_keyboard(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not _allowed(update.effective_user.id):
        return
    await update.message.reply_text(HELP_TEXT[:4000])


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not _allowed(update.effective_user.id):
        return
    chat_id = update.effective_chat.id
    agent = Agent(session_id=f"tg_{chat_id}")
    agent.terminal.approvals.clear_pending()
    _agents[chat_id] = agent
    _setup.pop(update.effective_user.id, None)
    await update.message.reply_text("Session reset.")


async def allow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not _allowed(update.effective_user.id):
        return
    agent = _get_agent(update.effective_chat.id)
    text = "Temporary full access — pick duration:"
    if agent.terminal.approvals.is_temp_allow_active():
        remaining = int(agent.terminal.approvals.temp_allow_remaining_seconds())
        text = f"Already on ({remaining // 60}m left). Pick new window:\n" + text
    await update.message.reply_text(text, reply_markup=_allow_window_keyboard())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user or not _allowed(query.from_user.id):
        if query:
            await query.answer("Not allowed", show_alert=True)
        return
    await query.answer()
    data = query.data or ""
    uid = query.from_user.id

    if data.startswith("prov:"):
        session = _setup.get(uid) or SetupSession()
        _setup[uid] = session
        msg = session.choose_provider(data.split(":", 1)[1])
        await query.edit_message_text(msg)
        return

    if data.startswith("allowwin:"):
        choice = data.split(":", 1)[1]
        agent = _get_agent(query.message.chat_id)
        if choice == "cancel":
            await query.edit_message_text("Cancelled.")
            return
        msg = agent.terminal.approvals.start_temp_allow(int(choice))
        await query.edit_message_text(msg)
        return

    agent = _get_agent(query.message.chat_id)
    if data.startswith("allow:"):
        result = agent.terminal.approve_and_run(data.split(":", 1)[1])
        await query.edit_message_text(f"Allowed once\n\n{result[:3500]}")
    elif data.startswith("session:"):
        agent.terminal.approvals.allow_session()
        result = agent.terminal.approve_and_run(data.split(":", 1)[1])
        await query.edit_message_text(f"Session allow\n\n{result[:3500]}")
    elif data.startswith("always:"):
        result = agent.terminal.always_allow_and_run(data.split(":", 1)[1])
        await query.edit_message_text(f"Always Allow\n\n{result[:3500]}")
    elif data.startswith("deny:"):
        msg = agent.terminal.deny(data.split(":", 1)[1])
        await query.edit_message_text(f"{msg}\nNo action taken.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    if not user or not _allowed(user.id):
        return

    text = update.message.text.strip()
    if not text:
        return

    session = _setup.get(user.id)
    if session and session.step != "done":
        if session.step == "base_url":
            await update.message.reply_text(session.set_base_url(text))
            return
        if session.step == "api_key":
            try:
                await update.message.delete()
            except Exception:
                pass
            await update.message.reply_text(session.set_api_key(text))
            return
        if session.step in ("model", "model_manual"):
            msg = session.choose_model(text)
            if session.step == "done":
                _setup.pop(user.id, None)
            await update.message.reply_text(msg)
            return

    username = user.username or user.first_name or ""
    await update.message.chat.send_action("typing")
    agent = None
    try:
        agent = _get_agent(update.effective_chat.id)
        reply = agent.chat(text, platform_username=username)
    except ValueError as e:
        reply = f"{e}\nRun /setup to configure provider + key + model."
    except Exception as e:
        logger.exception("Agent error")
        reply = f"Error: {type(e).__name__}"

    if "Command Approval Required" in (reply or ""):
        reply = f"{AGENT_FULL_NAME}: use the approval buttons below."
    await update.message.reply_text(reply[:4000])
    if agent is not None:
        await _send_pending_approvals(update, agent)
        await _send_outbound_files(update, agent)


async def _post_init(app: Application):
    async def _send(session_id: str, text: str):
        if not session_id.startswith("tg_"):
            return
        try:
            chat_id = int(session_id[len("tg_"):])
        except ValueError:
            return
        for i in range(0, max(len(text), 1), 4000):
            chunk = text[i : i + 4000]
            if chunk:
                await app.bot.send_message(chat_id=chat_id, text=chunk)
    asyncio.create_task(run_scheduler(_send))
    logger.info("cron scheduler task started")


def run():
    if not cfg.telegram_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required when GATEWAY=telegram")
    if cfg.require_allowlist and not cfg.allowed_telegram_ids:
        raise SystemExit("ALLOWED_TELEGRAM_IDS is required (REQUIRE_ALLOWLIST=true)")
    app = Application.builder().token(cfg.telegram_token).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("allow", allow_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Telegram gateway starting...")
    app.run_polling(drop_pending_updates=True)
