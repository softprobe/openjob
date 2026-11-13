"""Build the public JSON index consumed by the static site."""

from __future__ import annotations

import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from validator.constants import REPO
from validator.posts import (
    company_logo,
    company_website,
    effective_expiry,
    index_validator,
    is_unpublished,
    iter_post_files,
    job_contact_links,
    load_post,
    validate_tree,
    _company_page_path,
)
from validator.prose import excerpt as prose_excerpt
from validator.publish import write_discovery
from validator.share import permalink, render_post_page, share_links, share_text

# A company page links its newest roles. The jobs archive lists every role.
_OPEN_JOBS_ON_PAGE = 100


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
        posts.append(_project(rel, meta, body, root=root))
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
    jobs_for_company = _jobs_for_company(document["posts"])
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
        view = dict(post)
        if post.get("kind") == "company":
            jobs = jobs_for_company.get(str(post.get("permalink") or ""), [])
            view["open_jobs"] = jobs[:_OPEN_JOBS_ON_PAGE]
            extra = len(jobs) - len(view["open_jobs"])
            if extra:
                view["open_jobs_more"] = extra
        dest.write_text(render_post_page(view, body), encoding="utf-8")
        md = dest.parent / "index.md"
        md.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        count += 1
    write_discovery(site_dir, document)
    return count


def _jobs_for_company(posts: list[dict]) -> dict[str, list[dict]]:
    """Jobs grouped by company permalink. One pass, newest first."""
    grouped: dict[str, list[dict]] = {}
    for post in posts:
        if post.get("kind") != "job":
            continue
        company = post.get("company_permalink")
        if isinstance(company, str) and company:
            grouped.setdefault(company, []).append(post)
    return grouped


def _project(rel: str, meta: dict, body: str, *, root: Path) -> dict:
    kind = meta["kind"]
    owner = meta.get("github") if kind in {"talent", "talent-ref"} else meta.get("posted_by")
    expires = effective_expiry(meta)
    https_apply: str | None = None
    mailto: str | None = None
    if kind == "job":
        title = meta["title"]
        headline = meta["company_name"]
        org = meta["company_name"]
        role = meta["title"]
        https_apply, mailto = job_contact_links(meta)
        url = https_apply or _https_url(meta.get("website")) or _https_url(company_website(root, meta)) or ""
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
        "apply": https_apply,
        "apply_email": mailto,
        "logo": _logo(kind, meta, root),
        "careers": meta.get("careers"),
        "open_to": list(meta.get("open_to") or []),
        "compensation": meta.get("compensation") or "",
        "excerpt": prose_excerpt(body),
        "org_website": _org_website(kind, meta, root),
        "company_permalink": _company_permalink(kind, meta, root),
        "permalink": page,
        "share_text": blurb,
        "shares": share_links(blurb, page),
    }


def _logo(kind: str, meta: dict, root: Path) -> str | None:
    """Company pages use their own logo. Jobs use the logo on that company's page."""
    if kind == "company":
        return _https_url(meta.get("logo"))
    if kind == "job":
        return company_logo(root, meta.get("company"))
    return None


def _https_url(value: object) -> str | None:
    if isinstance(value, str) and value.startswith("https://") and not any(char.isspace() for char in value):
        return value
    return None


def _remote(value: object) -> str:
    if value is True:
        return "remote"
    if value is False:
        return "onsite"
    if value == "hybrid":
        return "hybrid"
    return "unspecified"


def _org_website(kind: str, meta: dict, root: Path) -> str | None:
    if kind == "job":
        return company_website(root, meta)
    if kind == "company":
        return _https_url(meta.get("website"))
    return None


def _company_permalink(kind: str, meta: dict, root: Path) -> str | None:
    if kind != "job":
        return None
    page = _company_page_path(root, meta.get("company"))
    if page is None:
        return None
    return permalink(page.relative_to(root).as_posix())


def _validate_index(document: dict) -> None:
    validator: Draft202012Validator = index_validator()
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        rendered = "\n".join(
            "/".join(str(part) for part in error.absolute_path) + f": {error.message}" for error in errors
        )
        raise ValueError(f"Index does not match schema/index.schema.json.\n{rendered}")
