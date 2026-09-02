# Setup guide

## Requirements

- Python 3.10+
- Discord **or** Telegram bot token
- An AI provider API key (added via `/setup` after start)

## Environment variables

See `.env.example`.

**Required to start the process:**
- `GATEWAY` = `discord` or `telegram`
- Matching bot token
- Matching `ALLOWED_*_IDS` (your numeric user id)

**Not required in `.env` if you use `/setup`:**
- Provider API keys (stored in `data/runtime_provider.json`)

## Optional

```env
ENABLE_GITHUB_ISSUES=false
GITHUB_PAT=
GITHUB_ISSUES_REPO=Aj-Niplex/Niplex-Harness-Public
```

Leave issues **false** unless you want sanitized crash reports opened on GitHub.

## Folder layout (important)

```
vault/          # your Obsidian-ready notes (safe for agent writes)
data/           # runtime state (gitignored)
agent/          # core — protected
gateway/        # Discord / Telegram — protected
```

## After first run

1. `/setup`  
2. `/help`  
3. Ask the agent to create a note under `vault/` and open it in Obsidian
