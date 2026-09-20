"""Git / GitHub category tools. Requires GITHUB_PAT and git_tools package."""
from __future__ import annotations
from typing import Any, Dict

from tools.registry import tool


def _git():
    try:
        import git_tools
        return git_tools
    except ImportError:
        return None


@tool({"type": "function", "function": {"name": "git_list_repos", "description": "List your GitHub repos", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}}}})
def git_list_repos(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available. Set GITHUB_PAT and ensure git_tools package is present."
    return g.git_list_repos(args.get("limit", 20))


@tool({"type": "function", "function": {"name": "git_list_files", "description": "List files at a path in a GitHub repo", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "path": {"type": "string", "default": ""}}, "required": ["repo"]}}})
def git_list_files(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available."
    return g.git_list_files(args.get("repo", ""), args.get("path", ""))


@tool({"type": "function", "function": {"name": "git_read_file", "description": "Read a file from a GitHub repo", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "path": {"type": "string"}}, "required": ["repo", "path"]}}})
def git_read_file(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available."
    return g.git_read_file(args.get("repo", ""), args.get("path", ""))


@tool({"type": "function", "function": {"name": "git_list_issues", "description": "List issues in a GitHub repo", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"}, "limit": {"type": "integer", "default": 15}}, "required": ["repo"]}}})
def git_list_issues(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available."
    return g.git_list_issues(args.get("repo", ""), args.get("state", "open"), args.get("limit", 15))


@tool({"type": "function", "function": {"name": "git_create_issue", "description": "Open a new issue", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string", "default": ""}}, "required": ["repo", "title"]}}})
def git_create_issue(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available."
    return g.git_create_issue(args.get("repo", ""), args.get("title", ""), args.get("body", ""))


@tool({"type": "function", "function": {"name": "git_list_commits", "description": "List recent commits", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "branch": {"type": "string", "default": "main"}, "limit": {"type": "integer", "default": 10}}, "required": ["repo"]}}})
def git_list_commits(agent: Any, args: Dict[str, Any]) -> str:
    g = _git()
    if not g:
        return "git_tools not available."
    return g.git_list_commits(args.get("repo", ""), args.get("branch", "main"), args.get("limit", 10))
