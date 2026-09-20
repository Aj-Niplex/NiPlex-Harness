# NiPlex Harness

**NiPlex Agent** — personal AI agent harness controlled from **Discord** or **Telegram**.

Built for people on free hosts (e.g. HidenCloud) **without a PC** — phone is the control panel.

**Dev / private experiments:** [dev-Niplex-Harness](https://github.com/Aj-Niplex/dev-Niplex-Harness) (private)

---

## What you get

- Discord (recommended) or Telegram gateway  
- `/setup` — provider → API key → models from API  
- Built-in Python sandbox + **approval buttons**  
- `vault/` — Obsidian-ready Markdown  
- Memory, files, skills, web search, terminal  
- Allow-list only; GitHub crash reports **off** by default  

---

## 5-minute start

1. Create a Discord or Telegram bot token  
2. Copy `.env.example` → `.env` and set token + your user id  
3. `pip install -r requirements.txt` && `python launch.py`  
4. In chat: **`/setup`** then **`/help`**

Full guides: [docs/HELP.md](docs/HELP.md) · [docs/SETUP.md](docs/SETUP.md)

---

## HidenCloud / free hosts

Python server → upload repo → `.env` → start: `python launch.py` → `/setup` in Discord/Telegram.

---

## Source of truth

| Role | Repo |
|------|------|
| **Public (this repo)** | Docs + cleaned source ready for users / future PyPI |
| **Private dev** | Full source + AI-handover + experiments |

Private data, AI agent notes, and internal tooling stay only in the private repo.

---

Built for Adarsh · Powered by **NiPlex Harness**
