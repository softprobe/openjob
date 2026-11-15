"""The seven OpenJob tools. Read tools use the public index. Write tools need GITHUB_TOKEN."""

from __future__ import annotations

import os
from typing import Any

from openjob_mcp.github import GitHub
from openjob_mcp.index_client import fetch_index, get_job, get_talent, search_jobs, search_talent
from openjob_mcp.posts import UPSTREAM, job_path_from_id, render, validate_markdown

TOOLS = (
    {
        "name": "search_jobs",
        "description": "Search live jobs on the public OpenJob index. No token. filters may set location, remote, language, tag, and employment_type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"},
            },
        },
    },
    {
        "name": "get_job",
        "description": "Fetch one live job by repository path or permalink. No token.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "search_talent",
        "description": "Search live talent profiles. No token. filters may set location, remote, language, tag, and open_to.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"},
            },
        },
    },
    {
        "name": "get_talent",
        "description": "Fetch one talent profile by GitHub login. No token.",
        "inputSchema": {
            "type": "object",
            "properties": {"login": {"type": "string"}},
            "required": ["login"],
        },
    },
    {
        "name": "validate_post",
        "description": "Check a job, talent, or company Markdown file with the OpenJob checker. No token and no pull request.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["job", "talent", "company"]},
                "markdown": {"type": "string"},
            },
            "required": ["kind", "markdown"],
        },
    },
    {
        "name": "create_or_update_post",
        "description": "Build one Markdown post and open or update a pull request as the person. Needs GITHUB_TOKEN. Forks when that login cannot push. One post per pull request. Sets the filename, posted_by, github, and owners from that login. Pass dry_run true to return the file without calling GitHub.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["job", "talent", "company"]},
                "fields": {"type": "object"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["kind", "fields"],
        },
    },
    {
        "name": "close_job",
        "description": "Open a pull request that removes a job. Needs GITHUB_TOKEN. Pass dry_run true to return the path without calling GitHub.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["id"],
        },
    },
)


def call_tool(name: str, arguments: dict | None, *, github: GitHub | None = None, posts: list[dict] | None = None) -> dict[str, Any]:
    args = arguments or {}
    if name == "search_jobs":
        return {"ok": True, "posts": search_jobs(args.get("query") or "", _filters(args), posts=posts)}
    if name == "get_job":
        post = get_job(str(args.get("id") or ""), posts=posts)
        return {"ok": post is not None, "post": post}
    if name == "search_talent":
        return {"ok": True, "posts": search_talent(args.get("query") or "", _filters(args), posts=posts)}
    if name == "get_talent":
        post = get_talent(str(args.get("login") or ""), posts=posts)
        return {"ok": post is not None, "post": post}
    if name == "validate_post":
        issues = validate_markdown(str(args.get("kind") or ""), str(args.get("markdown") or ""))
        return {"ok": not issues, "issues": issues}
    if name == "create_or_update_post":
        return create_or_update_post(
            str(args.get("kind") or ""),
            args.get("fields") or {},
            dry_run=bool(args.get("dry_run")),
            github=github,
        )
    if name == "close_job":
        return close_job(str(args.get("id") or ""), dry_run=bool(args.get("dry_run")), github=github)
    return {"ok": False, "error": f"Unknown tool {name}."}


def create_or_update_post(
    kind: str,
    fields: dict,
    *,
    dry_run: bool = False,
    github: GitHub | None = None,
    author: str | None = None,
) -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not dry_run and github is None and not token:
        return {"ok": False, "error": "Set GITHUB_TOKEN to open a pull request as the person."}
    login = author or "octocat"
    client = github
    if not dry_run:
        client = github or GitHub(token)
        login = client.login()
    elif author is None and isinstance(fields, dict):
        login = str(fields.get("posted_by") or fields.get("github") or login)
    try:
        path, markdown = render(kind, fields, login)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if not dry_run and client is not None:
        path, markdown = _preserve_posted_by(client, kind, fields, login, path, markdown)
    issues = validate_markdown(kind, markdown, author=login, path=path)
    if issues:
        return {"ok": False, "path": path, "markdown": markdown, "issues": issues}
    if dry_run:
        return {"ok": True, "dry_run": True, "path": path, "markdown": markdown, "pull_request": None}
    assert client is not None
    pull = client.open_file_pr(
        path=path,
        content=markdown,
        title=f"Add {path}",
        body=_pr_body(path),
    )
    return {"ok": True, "path": path, "markdown": markdown, "pull_request": pull}


def close_job(identifier: str, *, dry_run: bool = False, github: GitHub | None = None) -> dict[str, Any]:
    try:
        path = job_path_from_id(identifier)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if dry_run:
        return {"ok": True, "dry_run": True, "action": "delete", "path": path, "pull_request": None}
    token = os.environ.get("GITHUB_TOKEN", "")
    if github is None and not token:
        return {"ok": False, "error": "Set GITHUB_TOKEN to open a pull request as the person."}
    client = github or GitHub(token)
    pull = client.open_file_pr(
        path=path,
        content="",
        title=f"Close {path}",
        body=f"Remove `{path}` from the board.\n",
        delete=True,
    )
    return {"ok": True, "action": "delete", "path": path, "pull_request": pull}


def _preserve_posted_by(client: GitHub, kind: str, fields: dict, login: str, path: str, markdown: str) -> tuple[str, str]:
    """An edit keeps the original posted_by. The checker rejects a change to that field."""
    upstream = client.request("GET", f"/repos/{UPSTREAM}")
    default = "main"
    if isinstance(upstream, dict) and upstream.get("default_branch"):
        default = str(upstream["default_branch"])
    existing = client.file_text(path, default)
    if not existing:
        return path, markdown
    from openjob_mcp.posts import configure_import

    configure_import()
    from validator.posts import PostParseError, parse_post

    try:
        meta, _body = parse_post(existing)
    except PostParseError:
        return path, markdown
    previous = meta.get("posted_by")
    if not previous:
        return path, markdown
    edited = dict(fields)
    edited["posted_by"] = previous
    edited["path"] = path
    return render(kind, edited, login, updating=True)


def _filters(args: dict) -> dict:
    filters = dict(args.get("filters") or {})
    for key in ("location", "remote", "language", "tag", "employment_type", "open_to"):
        if args.get(key):
            filters[key] = args[key]
    return filters


def _pr_body(path: str) -> str:
    return (
        f"Add `{path}`.\n\n"
        "One post in this pull request. The filename, `posted_by`, `github`, and `owners` "
        "match the GitHub login that opened it.\n"
    )
