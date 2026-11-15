"""Indexed shards join the catalog as facts, behind owner posts."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))

from indexer.catalog import INDEXED_NOTICE  # noqa: E402
from openjob_mcp.index_client import search_jobs  # noqa: E402
from validator.index import build_index  # noqa: E402

NOW = datetime(2026, 11, 15, 6, 0, tzinfo=timezone.utc)


class CatalogTests(unittest.TestCase):
    def test_indexed_jobs_are_facts_and_owner_posts_stay_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            shard = data / "shards" / "greenhouse"
            shard.mkdir(parents=True)
            (shard / "acme.json").write_text(
                json.dumps(_shard(status="ok", failed_at=None, checked=NOW)),
                encoding="utf-8",
            )
            hidden = data / "shards" / "lever"
            hidden.mkdir()
            (hidden / "old.json").write_text(
                json.dumps(
                    _shard(
                        ats="lever",
                        board="old",
                        status="stale",
                        failed_at=NOW - timedelta(hours=49),
                        checked=NOW - timedelta(hours=49),
                        job_id="gone",
                    )
                ),
                encoding="utf-8",
            )
            document = build_index(ROOT, today=NOW.date(), index_data=data)
        jobs = [post for post in document["posts"] if post["kind"] == "job"]
        indexed = [post for post in jobs if post.get("origin") == "indexed"]
        self.assertEqual(document["indexed_notice"], INDEXED_NOTICE)
        self.assertEqual(len(indexed), 1)
        self.assertLess(jobs.index(next(post for post in jobs if post["origin"] == "owner")), jobs.index(indexed[0]))
        row = indexed[0]
        self.assertIsNone(row["permalink"])
        self.assertEqual(row["source_url"], "https://boards.example/live")
        self.assertNotIn("description", row)
        self.assertNotIn("phone", json.dumps(row).lower())
        found = search_jobs("", {"origin": "indexed"}, posts=document["posts"])
        self.assertEqual(found[0]["ats"], "greenhouse")
        self.assertEqual(found[0]["origin"], "indexed")
        self.assertEqual(search_jobs("", {"origin": "owner"}, posts=document["posts"])[0]["origin"], "owner")


def _shard(*, status, failed_at, checked, ats="greenhouse", board="acme", job_id="live") -> dict:
    stamp = checked.strftime("%Y-%m-%dT%H:%M:%SZ")
    failed = failed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if failed_at else None
    return {
        "ats": ats,
        "board": board,
        "slug": "acme",
        "name": "Acme",
        "website": "https://acme.example",
        "status": status,
        "checked_at": stamp,
        "failed_at": failed,
        "jobs": [
            {
                "id": job_id,
                "title": "Engineer",
                "company": "Acme",
                "location": "Remote",
                "remote": "remote",
                "department": "Research",
                "employment_type": "FULL_TIME",
                "salary_text": "100000 USD",
                "salary_source": ats,
                "posted": "2026-11-01",
                "updated": "",
                "deadline": "",
                "source_url": f"https://boards.example/{job_id}",
                "apply_url": f"https://boards.example/{job_id}",
                "first_seen": stamp,
                "last_checked": stamp,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
