"""Apply one fetch to the last snapshot.

A job that is missing from a successful feed is closed and dropped.
A failed feed keeps the last snapshot and is marked stale. The caller hides
a board that has been stale for 48 hours.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

STALE_AFTER = timedelta(hours=48)


def reconcile(previous: dict | None, outcome: dict, now: datetime) -> dict:
    """Return the next shard.

    ``outcome`` is ``{"ok": True, "jobs": [...], "etag": "..."}`` or
    ``{"ok": False}``. A 304 is ``{"ok": True, "not_modified": True, "etag": "..."}``.
    """
    stamp = _stamp(now)
    base = dict(previous or {})
    if outcome.get("ok") and outcome.get("not_modified"):
        jobs = [_touch(job, stamp) for job in base.get("jobs") or []]
        return _ok(base, jobs, stamp, outcome.get("etag") or base.get("etag"))
    if outcome.get("ok"):
        incoming = {job["id"]: job for job in outcome.get("jobs") or []}
        kept = []
        for job in incoming.values():
            old = _find(base.get("jobs") or [], job["id"])
            row = dict(job)
            row["first_seen"] = (old or {}).get("first_seen") or stamp
            row["last_checked"] = stamp
            kept.append(row)
        kept.sort(key=lambda job: job["id"])
        return _ok(base, kept, stamp, outcome.get("etag"))
    failed_at = base.get("failed_at") or stamp
    return {
        **base,
        "status": "stale",
        "checked_at": base.get("checked_at") or "",
        "failed_at": failed_at,
        "jobs": list(base.get("jobs") or []),
    }


def visible(shard: dict, now: datetime) -> bool:
    """False when a failing feed has been stale for 48 hours."""
    if shard.get("status") != "stale":
        return True
    failed = _parse(shard.get("failed_at"))
    if failed is None:
        return False
    return now - failed < STALE_AFTER


def platform_drop(before: dict[str, int], after: dict[str, int]) -> list[str]:
    """ATS names whose live count fell by half or more, from at least 20 jobs."""
    dropped = []
    for ats, count in before.items():
        if count < 20:
            continue
        if after.get(ats, 0) * 2 <= count:
            dropped.append(ats)
    return sorted(dropped)


def _ok(base: dict, jobs: list[dict], stamp: str, etag: object) -> dict:
    return {
        **base,
        "status": "ok",
        "checked_at": stamp,
        "failed_at": None,
        "etag": etag or None,
        "jobs": jobs,
    }


def _touch(job: dict, stamp: str) -> dict:
    row = dict(job)
    row["last_checked"] = stamp
    row.setdefault("first_seen", stamp)
    return row


def _find(jobs: list[dict], job_id: str) -> dict | None:
    for job in jobs:
        if job.get("id") == job_id:
            return job
    return None


def _stamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
