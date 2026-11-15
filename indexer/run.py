"""Fetch every reviewed board and write shards. A sharp drop is not published."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from indexer.client import fetch_board
from indexer.reconcile import platform_drop, reconcile, visible
from indexer.sources import load_sources


def run(
    sources_dir: Path,
    data_dir: Path,
    *,
    now: datetime | None = None,
    fetch=fetch_board,
    sleep=None,
    root: Path | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    sources = [
        source
        for source in load_sources(sources_dir)
        if source["slug"] not in indexing_off(root)
    ]
    previous = read_shards(data_dir)
    before = _counts(previous, now)
    nxt: dict[tuple[str, str], dict] = {}
    for index, source in enumerate(sources):
        if index and sleep is not None:
            sleep(1)
        key = (source["ats"], source["board"])
        prior = previous.get(key)
        outcome = fetch(source, (prior or {}).get("etag"))
        shard = reconcile(prior, outcome, now)
        shard.update(
            {
                "ats": source["ats"],
                "board": source["board"],
                "slug": source["slug"],
                "name": source["name"],
                "website": source["website"],
            }
        )
        nxt[key] = shard
    after = _counts(nxt, now)
    dropped = platform_drop(before, after)
    hidden = [
        {"ats": shard["ats"], "board": shard["board"], "slug": shard["slug"]}
        for shard in nxt.values()
        if not visible(shard, now)
    ]
    report = {
        "generated": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publish": not dropped,
        "companies": len(sources),
        "jobs": sum(after.values()),
        "before": before,
        "after": after,
        "dropped": dropped,
        "hidden": hidden,
        "stale": [
            {"ats": shard["ats"], "board": shard["board"], "slug": shard["slug"]}
            for shard in nxt.values()
            if shard.get("status") == "stale"
        ],
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    if dropped:
        _write_report(data_dir, report)
        return report
    _write_shards(data_dir, nxt)
    _write_report(data_dir, report)
    return report


def read_shards(data_dir: Path) -> dict[tuple[str, str], dict]:
    found = {}
    root = data_dir / "shards"
    if not root.is_dir():
        return found
    for path in root.glob("*/*.json"):
        shard = json.loads(path.read_text(encoding="utf-8"))
        found[(shard["ats"], shard["board"])] = shard
    return found


def indexing_off(root: Path | None) -> set[str]:
    """Company pages can set ``index: off`` after a claim."""
    if root is None:
        return set()
    found = set()
    for path in (root / "companies").glob("*/*.md"):
        meta = _front_matter(path)
        if _index_disabled(meta.get("index")) and meta.get("slug"):
            found.add(str(meta["slug"]))
    return found


def _counts(shards: dict[tuple[str, str], dict], now: datetime) -> dict[str, int]:
    counts: dict[str, int] = {}
    for shard in shards.values():
        if not visible(shard, now):
            continue
        counts[shard["ats"]] = counts.get(shard["ats"], 0) + len(shard.get("jobs") or [])
    return counts


def _write_shards(data_dir: Path, shards: dict[tuple[str, str], dict]) -> None:
    root = data_dir / "shards"
    root.mkdir(parents=True, exist_ok=True)
    keep = set()
    for (ats, board), shard in shards.items():
        path = root / ats / f"{board}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(shard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        keep.add(path.resolve())
    for path in root.glob("*/*.json"):
        if path.resolve() not in keep:
            path.unlink()


def _write_report(data_dir: Path, report: dict) -> None:
    (data_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _index_disabled(value: object) -> bool:
    # YAML reads the unquoted words on and off as booleans.
    if value is False:
        return True
    return str(value or "").strip().lower() in {"off", "false", "no"}


def _front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    raw = text.split("---", 2)[1]
    loaded = yaml.safe_load(raw)
    return loaded if isinstance(loaded, dict) else {}
