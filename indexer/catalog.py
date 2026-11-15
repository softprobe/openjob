"""Turn data-branch shards into index rows. No descriptions and no permalink pages."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

from indexer.reconcile import visible

INDEXED_NOTICE = (
    "Indexed rows are facts linked from the employer's own page. "
    "No license is granted on those rows. The employer owns the text. "
    "CC BY 4.0 covers posts under jobs/, talents/, and companies/ only."
)


def indexed_posts(data_dir: Path | None, *, now: datetime, owner_urls: set[str], claimed: set[str]) -> list[dict]:
    if data_dir is None or not data_dir.is_dir():
        return []
    posts = []
    root = data_dir / "shards"
    if not root.is_dir():
        return []
    for path in sorted(root.glob("*/*.json")):
        shard = json.loads(path.read_text(encoding="utf-8"))
        if not visible(shard, now):
            continue
        for job in shard.get("jobs") or []:
            url = job.get("apply_url") or job.get("source_url") or ""
            if url and url in owner_urls:
                continue
            posts.append(_row(shard, job, claimed=shard.get("slug") in claimed))
    return posts


def claimed_slugs(root: Path) -> set[str]:
    found = set()
    for path in (root / "companies").glob("*/*.md"):
        meta = _front_matter(path)
        owners = meta.get("owners") or []
        if meta.get("slug") and isinstance(owners, list) and owners:
            found.add(str(meta["slug"]))
    return found


def _row(shard: dict, job: dict, *, claimed: bool) -> dict:
    posted = job.get("posted") or (job.get("first_seen") or "")[:10] or "1970-01-01"
    company = job.get("company") or shard.get("name") or shard.get("slug")
    ats = shard["ats"]
    url = job.get("apply_url") or job["source_url"]
    salary = job.get("salary_text") or ""
    excerpt = f"Indexed from {company}'s {ats} board."
    employment = [job["employment_type"]] if job.get("employment_type") else None
    return {
        "kind": "job",
        "path": f"indexed/{ats}/{shard['board']}/{job['id']}",
        "owner": shard.get("slug") or "indexed",
        "title": job["title"],
        "headline": company,
        "org": company,
        "role": job["title"],
        "location": job.get("location") or "",
        "remote": job.get("remote") or "unspecified",
        "languages": [],
        "tags": [],
        "posted": posted,
        "expires": None,
        "federated": False,
        "url": url,
        "source_url": job.get("source_url") or url,
        "profile_url": None,
        "website": None,
        "linkedin": None,
        "apply": url,
        "apply_email": None,
        "logo": None,
        "careers": shard.get("website"),
        "open_to": [],
        "compensation": salary,
        "employment_type": employment,
        "salary": None,
        "locations": None,
        "excerpt": excerpt,
        "org_website": shard.get("website"),
        "company_permalink": None,
        "permalink": None,
        "share_text": excerpt,
        "shares": [],
        "origin": "indexed",
        "ats": ats,
        "board": shard.get("board"),
        "first_seen": job.get("first_seen"),
        "last_checked": job.get("last_checked") or shard.get("checked_at"),
        "salary_text": salary,
        "salary_source": job.get("salary_source") or None,
        "department": job.get("department") or "",
        "claimed": claimed,
        "indexed_id": job.get("id"),
    }


def _front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    loaded = yaml.safe_load(text.split("---", 2)[1])
    return loaded if isinstance(loaded, dict) else {}
