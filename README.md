# Niplex Harness

**NiPlex Agent** — a personal AI agent harness you control from **Discord** or **Telegram**.

Built for people who run agents on free hosts (e.g. HidenCloud) **without a PC** — your phone is the control panel.

---

## What you get

- **Gateway:** Discord (recommended) or Telegram  
- **Setup in chat:** `/setup` picks provider → API key → models from the API  
- **Sandbox:** built-in Python runner with **approval buttons** for risky code  
- **Vault:** `vault/` folder of plain Markdown — open it in **Obsidian**  
- **Tools:** memory, files, skills, web search, terminal, cron/sub-agent stubs  
- **Privacy:** allow-list user IDs; optional GitHub issue reports are **off** by default  

Identity is branded **NiPlex Agent / Niplex Harness** (hardcoded).

---

## 5-minute start

### 1. Get a bot token
- **Discord:** [Discord Developer Portal](https://discord.com/developers/applications) → Bot → token. Enable **Message Content Intent**. Invite bot with message permissions.  
- **Telegram:** talk to [@BotFather](https://t.me/BotFather) → `/newbot`.

### 2. Get your user ID
- Discord: Settings → Advanced → Developer Mode → right-click yourself → Copy User ID  
- Telegram: use a bot like `@userinfobot`

### 3. Configure

```bash
cp .env.example .env
```

Minimal `.env`:

```env
GATEWAY=discord
DISCORD_BOT_TOKEN=your_token
ALLOWED_DISCORD_IDS=123456789012345678
REQUIRE_ALLOWLIST=true
```

(For Telegram: `GATEWAY=telegram`, `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_IDS`.)

### 4. Run

```bash
pip install -r requirements.txt
python launch.py
```

### 5. In chat

```
/setup
```

Choose provider (Agnes / Google / OpenAI / Anthropic / OpenRouter / custom) → send API key → pick a model or type `random`.

Then say hello. Use **`/help`** anytime.

Full guide: [docs/HELP.md](docs/HELP.md) · [docs/SETUP.md](docs/SETUP.md)

---

## Approval buttons

Risky terminal actions show:

| Button | Meaning |
|--------|---------|
| Allow Once | Run this time only |
| Allow Session | Auto-allow for this session |
| Always Allow | Only **this exact command text** is free later |
| Deny | Cancel |

---

## HidenCloud (free Python)

1. Create a Python server  
2. Upload this repo  
3. Put `.env` in the root  
4. Startup command: `python launch.py`  
5. Open Discord/Telegram → `/setup`

---

## Security notes

- The agent **cannot** write files on the project root (must create a folder first).  
- Core harness paths cannot be deleted by tools.  
- Prefer notes under `vault/`.  
- Do not commit `.env` or `data/runtime_provider.json`.

---

## Dev vs public

- **Public (this repo):** stable docs + code for users  
- **Dev:** `Aj-Niplex/Niplex-Harness` (experiments; may be renamed `dev-Niplex-Harness`)

---

Built for Adarsh · Powered by **Niplex Harness**
