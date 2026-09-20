"""
Obsidian-ready memory system + keyword search + simple graph relations + vector stub.

- Global: data/global/*.md
- Session: data/sessions/<sid>/*.md
- Graph: simple JSON relations between notes
- Vector: optional external (or local keyword for free tier)
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import cfg


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")[:80] or "note"


class MemoryManager:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.global_dir = cfg.memory_root / "global"
        self.session_dir = cfg.memory_root / "sessions" / session_id
        self.graph_path = cfg.memory_root / "graph.json"
        self.global_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_seed("USER.md", "# User\n\n(Write durable facts about the user here.)\n")
        self._ensure_seed("MEMORY.md", "# Memory\n\n(High-level durable knowledge.)\n")
        if not self.graph_path.exists():
            self.graph_path.write_text(json.dumps({"nodes": [], "edges": []}, indent=2))

    def _ensure_seed(self, name: str, content: str):
        path = self.global_dir / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def _write_md(self, path: Path, title: str, body: str, meta: Optional[Dict[str, Any]] = None):
        meta = meta or {}
        meta.setdefault("created", _now())
        meta["updated"] = _now()
        front = yaml.dump(meta, default_flow_style=False, allow_unicode=True).strip()
        content = f"---\n{front}\n---\n\n# {title}\n\n{body.strip()}\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(cfg.memory_root))

    def save_memory(
        self,
        content: str,
        title: str = "Note",
        scope: str = "session",
        tags: Optional[List[str]] = None,
    ) -> str:
        tags = tags or []
        slug = _slug(title)
        path = (self.global_dir if scope == "global" else self.session_dir) / f"{slug}.md"
        rel = self._write_md(path, title=title, body=content, meta={"scope": scope, "tags": tags, "session_id": self.session_id})
        return f"Saved to {rel}"

    def search_memory(self, query: str, scope: str = "both", limit: int = 10) -> str:
        query_l = query.lower()
        results: List[str] = []
        dirs = []
        if scope in ("global", "both"):
            dirs.append(self.global_dir)
        if scope in ("session", "both"):
            dirs.append(self.session_dir)

        for d in dirs:
            if not d.exists():
                continue
            for p in sorted(d.glob("**/*.md")):
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                if query_l in text.lower():
                    lines = text.splitlines()
                    excerpt = "\n".join(lines[:25])
                    rel = p.relative_to(cfg.memory_root)
                    results.append(f"### {rel}\n{excerpt}\n")
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break
        return "\n---\n".join(results) if results else "No matching memory found."

    def list_memory(self, scope: str = "both") -> str:
        files = []
        if scope in ("global", "both"):
            files.extend(sorted(self.global_dir.glob("*.md")))
        if scope in ("session", "both"):
            files.extend(sorted(self.session_dir.glob("*.md")))
        if not files:
            return "No memory files yet."
        return "\n".join(str(f.relative_to(cfg.memory_root)) for f in files)

    def get_context_for_prompt(self, max_chars: int = 12000) -> str:
        parts = []
        for name in ("USER.md", "MEMORY.md"):
            p = self.global_dir / name
            if p.exists():
                parts.append(f"## {name}\n{p.read_text(encoding='utf-8')[:4000]}")
        session_files = sorted(self.session_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for p in session_files:
            parts.append(f"## session/{p.name}\n{p.read_text(encoding='utf-8')[:1500]}")
        return "\n\n".join(parts)[:max_chars]

    def graph_add_node(self, node_id: str, label: str, node_type: str = "note") -> str:
        data = json.loads(self.graph_path.read_text())
        for n in data["nodes"]:
            if n["id"] == node_id:
                n["label"] = label
                n["type"] = node_type
                self.graph_path.write_text(json.dumps(data, indent=2))
                return f"Updated node {node_id}"
        data["nodes"].append({"id": node_id, "label": label, "type": node_type})
        self.graph_path.write_text(json.dumps(data, indent=2))
        return f"Added node {node_id}"

    def graph_add_edge(self, source: str, target: str, relation: str = "related") -> str:
        data = json.loads(self.graph_path.read_text())
        data["edges"].append({"source": source, "target": target, "relation": relation})
        self.graph_path.write_text(json.dumps(data, indent=2))
        return f"Linked {source} -[{relation}]-> {target}"

    def graph_query(self, node_id: Optional[str] = None) -> str:
        data = json.loads(self.graph_path.read_text())
        if not node_id:
            return json.dumps(data, indent=2)[:8000]
        related = [e for e in data["edges"] if e["source"] == node_id or e["target"] == node_id]
        nodes = [n for n in data["nodes"] if n["id"] == node_id]
        return json.dumps({"node": nodes, "edges": related}, indent=2)

    def vector_search(self, query: str, limit: int = 5) -> str:
        return self.search_memory(query, scope="both", limit=limit) + "\n\n(Note: vector backend is keyword-fallback on free tier. Set VECTOR_DB_URL for real embeddings.)"
