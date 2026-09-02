# Help — using NiPlex Agent

## Commands

| Command | Description |
|---------|-------------|
| `/setup` | Configure AI provider, API key, and model |
| `/help` | Show help |
| `/reset` | Reset the agent session for this chat |

## Chat

- **Discord server:** mention the bot, e.g. `@YourBot what can you do?`
- **Discord DM or Telegram:** send a normal message

## `/setup` steps

1. **Provider** — Agnes, Google Gemini, OpenAI, Anthropic, OpenRouter, or custom OpenAI-compatible  
2. **API key** — paste once (bot tries to delete the message for privacy)  
3. **Model** — harness lists models from the provider; reply with a number, model id, or `random`

Keys are saved under `data/runtime_provider.json` (local, not for git).

## Files & Obsidian

- Notes go under **`vault/`** as normal `.md` files  
- Open the `vault` folder in Obsidian to browse/edit  
- Agent will not place files directly on the repo root

## Terminal safety

If a command is risky, use the **buttons under the embed** (not typed commands).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot ignores you | Check `ALLOWED_*_IDS` matches your user id |
| “Run /setup” | Provider not configured yet |
| Discord no replies | Enable **Message Content Intent** + mention bot in servers |
| Model list empty | Key/network issue — type a model id manually |

— NiPlex Agent · Niplex Harness
