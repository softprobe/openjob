"""Build the public JSON index consumed by the static site."""

from __future__ import annotations

import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from validator.constants import REPO
from validator.posts import (
    effective_expiry,
    index_validator,
    is_unpublished,
    iter_post_files,
    load_post,
    validate_tree,
)
from validator.share import permalink, render_post_page, share_links, share_text


def build_index(root: Path, *, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    issues = validate_tree(root, today=today)
    if issues:
        details = "\n".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"Refusing to index invalid posts.\n{details}")
    posts = []
    for rel, path in iter_post_files(root):
        # ``iter_post_files`` already skips these. The second check is here so
        # a future walk of the whole tree still cannot publish fixtures or
        # starting files.
        if is_unpublished(rel) or not rel.endswith(".md"):
            continue
        meta, body = load_post(path)
        posts.append(_project(rel, meta, body))
    posts.sort(key=lambda post: post["path"])
    posts.sort(key=lambda post: post["posted"], reverse=True)
    document = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": f"https://github.com/{REPO}",
        "posts": posts,
    }
    _validate_index(document)
    return document


def write_pages(root: Path, site_dir: Path, document: dict) -> int:
    """Write one static permalink page per post under ``site_dir/p/``.

    A previous ``p/`` directory is replaced so an expired post does not leave
    a stale page in the Pages artifact.
    """
    pages = site_dir / "p"
    if pages.is_symlink():
        raise ValueError("Refusing to replace a symlinked permalink directory.")
    if pages.exists():
        shutil.rmtree(pages)
    by_path = {post["path"]: post for post in document["posts"]}
    count = 0
    for rel, path in iter_post_files(root):
        if is_unpublished(rel):
            continue
        post = by_path.get(rel)
        if post is None:
            continue
        _meta, body = load_post(path)
        dest = site_dir / "p" / rel[:-3] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_post_page(post, body), encoding="utf-8")
        count += 1
    return count


def _project(rel: str, meta: dict, body: str) -> dict:
    kind = meta["kind"]
    owner = meta.get("github") if kind in {"talent", "talent-ref"} else meta.get("posted_by")
    expires = effective_expiry(meta)
    if kind == "job":
        title = meta["title"]
        headline = meta["company_name"]
        org = meta["company_name"]
        role = meta["title"]
        url = meta["apply"]
    elif kind in {"talent", "talent-ref"}:
        title = meta["name"]
        headline = meta["headline"]
        org = ""
        role = meta["headline"]
        url = meta.get("website") or meta.get("linkedin") or f"https://github.com/{meta['github']}"
        if kind == "talent-ref":
            url = meta["profile_url"]
    else:
        title = meta["name"]
        headline = ""
        org = meta["name"]
        role = meta["name"]
        url = meta.get("careers") or meta["website"]
    blurb = share_text(meta)
    page = permalink(rel)
    return {
        "kind": kind,
        "path": rel,
        "owner": owner,
        "title": title,
        "headline": headline,
        "org": org,
        "role": role,
        "location": meta.get("location") or "",
        "remote": _remote(meta.get("remote")),
        "languages": list(meta.get("languages") or []),
        "tags": list(meta.get("tags") or []),
        "posted": meta["posted"],
        "expires": expires.isoformat() if expires else None,
        "example": meta.get("example") is True,
        "federated": kind == "talent-ref",
        "url": url,
        "source_url": f"https://github.com/{REPO}/blob/main/{rel}",
        "profile_url": meta.get("profile_url"),
        "website": meta.get("website"),
        "linkedin": meta.get("linkedin"),
        "apply": meta.get("apply"),
        "careers": meta.get("careers"),
        "open_to": list(meta.get("open_to") or []),
        "compensation": meta.get("compensation") or "",
        "excerpt": _excerpt(body),
        "permalink": page,
        "share_text": blurb,
        "shares": share_links(blurb, page),
    }


def _remote(value: object) -> str:
    if value is True:
        return "remote"
    if value is False:
        return "onsite"
    if value == "hybrid":
        return "hybrid"
    return "unspecified"


def _excerpt(body: str, limit: int = 240) -> str:
    text = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    text = re.sub(r"[#>*_`\[\]]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _validate_index(document: dict) -> None:
    validator: Draft202012Validator = index_validator()
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        rendered = "\n".join(
            "/".join(str(part) for part in error.absolute_path) + f": {error.message}" for error in errors
        )
        raise ValueError(f"Index does not match schema/index.schema.json.\n{rendered}")
