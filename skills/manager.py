"""
Skills system with Super Skill registry.

Categories:
- personal/ — user workflow patterns
- market/   — skills from a future skill market
- custom/   — anything dropped in or downloaded

All go through size-cap + injection-pattern guard before saving.
"""
from __future__ import annotations
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from security.content_guard import scan_for_injection

SKILLS_DIR = Path(__file__).resolve().parent / "library"
SUPER_SKILL_PATH = SKILLS_DIR / "super-skill.md"

CATEGORIES = ("personal", "market", "custom")
DEFAULT_CATEGORY = "personal"

for _cat in CATEGORIES:
    (SKILLS_DIR / _cat).mkdir(parents=True, exist_ok=True)

MAX_SKILL_CHARS = 15_000


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")[:60] or "skill"


def _guard_content(content: str) -> Optional[str]:
    if len(content) > MAX_SKILL_CHARS:
        return (
            f"Skill content is {len(content)} chars, over the {MAX_SKILL_CHARS}-char "
            "limit. Split it into multiple skills or move bulk data to a vault/ file."
        )
    findings = scan_for_injection(content)
    if findings:
        return (
            "Refusing to save: content matches pattern(s) commonly seen in "
            f"prompt-injection attempts ({', '.join(findings)})."
        )
    return None


def _find_skill(name: str) -> Optional[Tuple[str, Path]]:
    name = name.strip()
    if "/" in name:
        cat, _, slug = name.partition("/")
        if cat in CATEGORIES:
            p = SKILLS_DIR / cat / f"{slug}.md"
            return (cat, p) if p.exists() else None
        return None
    for cat in CATEGORIES:
        p = SKILLS_DIR / cat / f"{name}.md"
        if p.exists():
            return cat, p
    return None


class SkillManager:
    def __init__(self):
        self._ensure_super_skill()

    def _ensure_super_skill(self):
        if not SUPER_SKILL_PATH.exists():
            SUPER_SKILL_PATH.write_text(
                """---
name: super-skill
tags: [core, registry]
---

# Super Skill — Central Registry

This file is the single source of truth for all skills and their use cases.

| Skill | Category | Use Case |
|-------|----------|----------|
| niplex-identity | personal | Hard identity of the agent |
| obsidian-memory | personal | How to use global vs session memory |
""",
                encoding="utf-8",
            )

    def list_skills(self) -> List[str]:
        out = []
        for cat in CATEGORIES:
            for p in sorted((SKILLS_DIR / cat).glob("*.md")):
                out.append(f"{cat}/{p.stem}")
        return out

    def load_skill(self, name: str) -> str:
        found = _find_skill(name)
        if not found:
            return f"Skill '{name}' not found. Available: {', '.join(self.list_skills()) or 'none'}"
        category, path = found
        return path.read_text(encoding="utf-8")

    def get_super_skill(self) -> str:
        return SUPER_SKILL_PATH.read_text(encoding="utf-8")

    def create_skill(self, name: str, content: str, use_case: str = "", category: str = DEFAULT_CATEGORY) -> str:
        content = content.strip()
        category = (category or DEFAULT_CATEGORY).strip().lower()
        if category not in CATEGORIES:
            return f"Unknown category '{category}'. Use one of: {', '.join(CATEGORIES)}"

        rejection = _guard_content(content)
        if rejection:
            return rejection

        slug = _slug(name)
        path = SKILLS_DIR / category / f"{slug}.md"
        if path.exists():
            return f"Skill '{category}/{slug}' already exists. Use edit_skill instead."

        market_line = ""
        if category == "market":
            market_line = f"market_id: {uuid.uuid4().hex[:10]}\n"

        body = f"""---
name: {slug}
category: {category}
created: {_now()}
created_by: agent
{market_line}use_case: {use_case or 'general'}
---

{content}

<!-- provenance: created {_now_iso()} by agent via create_skill -->
"""
        path.write_text(body, encoding="utf-8")
        self._register_in_super(category, slug, use_case or "general")
        return f"Created skill '{category}/{slug}' and registered in Super Skill"

    def edit_skill(self, name: str, content: str) -> str:
        if name == "super-skill":
            rejection = _guard_content(content)
            if rejection:
                return rejection
            SUPER_SKILL_PATH.write_text(content, encoding="utf-8")
            return "Super Skill registry updated"

        found = _find_skill(name)
        if not found:
            return f"Skill '{name}' not found"
        category, path = found

        content = content.strip()
        rejection = _guard_content(content)
        if rejection:
            return rejection

        stamped = f"{content}\n\n<!-- provenance: edited {_now_iso()} by agent via edit_skill -->\n"
        path.write_text(stamped, encoding="utf-8")
        return f"Edited skill '{category}/{path.stem}'"

    def search_skill(self, query: str) -> str:
        q = query.lower()
        hits = []
        for cat in CATEGORIES:
            for p in (SKILLS_DIR / cat).glob("*.md"):
                text = p.read_text(encoding="utf-8")
                if q in text.lower() or q in p.stem:
                    hits.append(f"- {cat}/{p.stem}")
        return "\n".join(hits) if hits else "No skills matched."

    def _register_in_super(self, category: str, slug: str, use_case: str):
        text = SUPER_SKILL_PATH.read_text(encoding="utf-8")
        if f"| {slug} |" in text:
            return
        line = f"| {slug} | {category} | {use_case} |\n"
        if text.rstrip().endswith("|"):
            SUPER_SKILL_PATH.write_text(text.rstrip() + "\n" + line, encoding="utf-8")
        else:
            SUPER_SKILL_PATH.write_text(text + "\n" + line, encoding="utf-8")
