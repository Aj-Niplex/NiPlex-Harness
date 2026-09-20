"""
# what this block
# Shared /help text for Discord and Telegram.
# why this code
# New users only have a bot token; this explains /setup and daily use.
# optional if u want
# Edit copy here; both gateways import it.
"""
from agent.identity import AGENT_FULL_NAME, HARNESS_NAME

HELP_TEXT = f"""**{AGENT_FULL_NAME}** · **{HARNESS_NAME}**

**First time**
1. `/setup` — choose provider → API key → model (or `random`)
2. Then chat normally

**Commands**
• `/setup` — AI provider + key + model
• `/help` — this message
• `/reset` — clear this session

**Chat**
• Discord server: **mention** the bot
• Discord DM / Telegram: just type

**Approvals**
Risky code shows buttons: Allow Once · Allow Session · Always Allow (exact command only) · Deny

**Files**
• Notes go in `vault/` (open in Obsidian)
• Agent cannot put files on the project root — it creates a folder first

**Privacy**
• Only your user id (allow-list) can talk to the bot
• GitHub crash reports are off unless you enable them in `.env`

More: see `docs/HELP.md` in the repo.
"""
