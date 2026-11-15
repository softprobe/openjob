"""Read the public OpenJob index. No token."""

from __future__ import annotations

import json
import os
import urllib.request

DEFAULT_INDEX = "https://openjob.softprobe.ai/index.json"

_KEEP = (
    "kind",
    "path",
    "permalink",
    "title",
    "headline",
    "org",
    "role",
    "location",
    "remote",
    "languages",
    "tags",
    "posted",
    "expires",
    "apply",
    "apply_email",
    "open_to",
    "employment_type",
    "compensation",
    "salary",
    "locations",
    "owner",
    "url",
    "website",
    "linkedin",
    "profile_url",
    "logo",
    "careers",
    "org_website",
    "company_permalink",
    "excerpt",
    "source_url",
    "federated",
)


def index_url() -> str:
    return os.environ.get("OPENJOB_INDEX") or DEFAULT_INDEX


def fetch_index(url: str | None = None) -> dict:
    target = url or index_url()
    request = urllib.request.Request(
        target,
        headers={"User-Agent": "openjob-mcp", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("posts"), list):
        raise ValueError("The index does not list posts.")
    return payload


def slim(post: dict) -> dict:
    return {key: post[key] for key in _KEEP if post.get(key) not in (None, "", [])}


def search_jobs(query: str = "", filters: dict | None = None, *, posts: list[dict] | None = None) -> list[dict]:
    return _search("job", query, filters, posts)


def search_talent(query: str = "", filters: dict | None = None, *, posts: list[dict] | None = None) -> list[dict]:
    found = _search("talent", query, filters, posts)
    found.extend(_search("talent-ref", query, filters, posts))
    return found


def get_job(identifier: str, *, posts: list[dict] | None = None) -> dict | None:
    return _get(identifier, {"job"}, posts)


def get_talent(login: str, *, posts: list[dict] | None = None) -> dict | None:
    wanted = login.strip().casefold()
    for post in _posts(posts):
        if post.get("kind") not in {"talent", "talent-ref"}:
            continue
        owner = str(post.get("owner") or "")
        path = str(post.get("path") or "")
        stem = path.rsplit("/", 1)[-1].removesuffix(".md")
        if owner.casefold() == wanted or stem.casefold() == wanted:
            return slim(post)
    return None


def _posts(posts: list[dict] | None) -> list[dict]:
    if posts is not None:
        return posts
    return fetch_index()["posts"]


def _search(kind: str, query: str, filters: dict | None, posts: list[dict] | None) -> list[dict]:
    rules = filters or {}
    needle = query.casefold().strip()
    found = []
    for post in _posts(posts):
        if post.get("kind") != kind:
            continue
        if needle and needle not in _haystack(post):
            continue
        if not _filters(post, rules):
            continue
        found.append(slim(post))
    return found


def _get(identifier: str, kinds: set[str], posts: list[dict] | None) -> dict | None:
    wanted = _normalize_id(identifier)
    for post in _posts(posts):
        if post.get("kind") not in kinds:
            continue
        candidates = {
            _normalize_id(str(post.get("path") or "")),
            _normalize_id(str(post.get("permalink") or "")),
        }
        if wanted in candidates:
            return slim(post)
    return None


def _normalize_id(value: str) -> str:
    text = value.strip()
    marker = "/p/"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.split("?", 1)[0].split("#", 1)[0].strip("/")
    if text.endswith(".md"):
        text = text[:-3]
    return text.casefold()


def _haystack(post: dict) -> str:
    parts = [
        post.get("title"),
        post.get("headline"),
        post.get("org"),
        post.get("role"),
        post.get("location"),
        post.get("excerpt"),
        post.get("path"),
        post.get("owner"),
    ]
    tags = post.get("tags") or []
    if isinstance(tags, list):
        parts.extend(tags)
    return " ".join(str(part) for part in parts if part).casefold()


def _filters(post: dict, rules: dict) -> bool:
    location = str(rules.get("location") or "").casefold()
    if location and location not in str(post.get("location") or "").casefold():
        return False
    remote = str(rules.get("remote") or "").casefold()
    if remote and remote != str(post.get("remote") or "").casefold():
        return False
    language = str(rules.get("language") or "")
    if language and language not in (post.get("languages") or []):
        return False
    tag = str(rules.get("tag") or "")
    if tag and tag not in (post.get("tags") or []):
        return False
    if not _listed(post.get("employment_type"), rules.get("employment_type")):
        return False
    if not _listed(post.get("open_to"), rules.get("open_to")):
        return False
    return True


def _listed(value: object, wanted: object) -> bool:
    if not wanted:
        return True
    target = str(wanted)
    if isinstance(value, list):
        return target in value
    return str(value or "") == target
