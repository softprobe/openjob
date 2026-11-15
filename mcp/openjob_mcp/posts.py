"""Build a post and run it through the OpenJob checker."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

UPSTREAM = "softprobe/openjob"
KINDS = ("job", "talent", "company")


def repo_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "schema" / "job.schema.json").is_file() and (parent / "validator" / "posts.py").is_file():
            return parent
    return None


def configure_import() -> None:
    """Make `validator` importable from a checkout or from the installed schema copy."""
    root = repo_root()
    if root is not None:
        root_text = str(root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        return
    bundled = Path(__file__).resolve().parent / "schema"
    if (bundled / "job.schema.json").is_file():
        os.environ.setdefault("OPENJOB_SCHEMA", str(bundled))


def render(kind: str, fields: dict, login: str, *, updating: bool = False) -> tuple[str, str]:
    """Return the repository path and the Markdown file."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of: {', '.join(KINDS)}")
    meta = {key: value for key, value in fields.items() if key not in {"body", "path"} and value is not None}
    meta["kind"] = kind
    today = datetime.now(timezone.utc).date().isoformat()
    meta.setdefault("posted", today)
    if kind == "job":
        if not updating:
            meta["posted_by"] = login
        path = _job_path(meta, fields.get("path"))
    elif kind == "talent":
        meta["github"] = login
        path = f"talents/{login}.md"
    else:
        owners = [str(item) for item in (meta.get("owners") or [])]
        if login not in owners:
            owners.insert(0, login)
        meta["owners"] = owners
        if not updating:
            meta["posted_by"] = login
        slug = str(meta.get("slug") or "")
        if not slug:
            raise ValueError("A company post needs slug.")
        path = fields.get("path") or f"companies/{slug[0]}/{slug}.md"
    body = str(fields.get("body") or "").strip()
    dumped = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    markdown = f"---\n{dumped}\n---\n\n{body}\n"
    return str(path), markdown


def validate_markdown(kind: str, markdown: str, *, author: str | None = None, path: str | None = None) -> list[dict]:
    configure_import()
    from validator.posts import parse_post, validate_post
    from validator.posts import PostParseError

    try:
        meta, _body = parse_post(markdown)
    except PostParseError as exc:
        return [{"code": "front-matter", "path": path or kind, "message": str(exc), "fix": ""}]
    rel = path or _path_for(kind, meta, author)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
        issues = validate_post(
            root=root,
            rel=rel,
            today=datetime.now(timezone.utc).date(),
            author=author,
            new_file=True,
        )
    return [
        {"code": issue.code, "path": issue.path, "message": issue.message, "fix": issue.fix}
        for issue in issues
    ]


def job_path_from_id(identifier: str) -> str:
    text = identifier.strip()
    marker = "/p/"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.split("?", 1)[0].split("#", 1)[0].strip("/")
    if not text.endswith(".md"):
        text = f"{text}.md"
    if not text.startswith("jobs/"):
        raise ValueError("close_job needs a job path or a job permalink.")
    return text


def _job_path(meta: dict, explicit: object) -> str:
    if explicit:
        return str(explicit)
    posted = str(meta.get("posted") or "")
    year, month = posted[:4], posted[5:7]
    company = str(meta.get("company") or "")
    role = str(meta.get("role_slug") or "")
    if not (year.isdigit() and month.isdigit() and company and role):
        raise ValueError("A job needs posted, company, and role_slug, or an explicit path.")
    return f"jobs/{year}/{month}/{company}-{role}.md"


def _path_for(kind: str, meta: dict, author: str | None) -> str:
    if kind == "talent":
        login = str(meta.get("github") or author or "login")
        return f"talents/{login}.md"
    if kind == "company":
        slug = str(meta.get("slug") or "company")
        return f"companies/{slug[:1]}/{slug}.md"
    return _job_path(meta, None)
