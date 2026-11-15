"""The runner writes shards, skips a claimed opt-out, and holds a sharp drop."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from indexer import USER_AGENT
from indexer.client import build_request
from indexer.run import run

NOW = datetime(2026, 11, 15, 6, 0, tzinfo=timezone.utc)


def _source(slug: str, ats: str = "greenhouse") -> dict:
    return {
        "slug": slug,
        "name": slug.title(),
        "website": f"https://{slug}.example",
        "ats": ats,
        "board": slug,
    }


def _job(job_id: str) -> dict:
    return {
        "id": job_id,
        "title": "Engineer",
        "company": "Acme",
        "location": "Remote",
        "remote": "remote",
        "department": "",
        "employment_type": "FULL_TIME",
        "salary_text": "",
        "salary_source": "",
        "posted": "2026-11-01",
        "updated": "",
        "deadline": "",
        "source_url": f"https://boards.example/{job_id}",
        "apply_url": f"https://boards.example/{job_id}",
    }


class RunTests(unittest.TestCase):
    def test_requests_identify_openjob_and_carry_no_token(self) -> None:
        request = build_request("https://boards-api.greenhouse.io/v1/boards/acme/jobs", "abc")
        self.assertEqual(request.get_header("User-agent"), USER_AGENT)
        self.assertIn("openjob.softprobe.ai/about#index", USER_AGENT)
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(request.get_header("If-none-match"), "abc")

    def test_a_run_writes_shards_and_waits_between_boards(self) -> None:
        waits = []

        def fetch(source, etag):
            return {"ok": True, "jobs": [_job(source["slug"])], "etag": "1"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources"
            sources.mkdir()
            data = root / "data"
            for slug in ("acme", "beta"):
                (sources / f"{slug}.yml").write_text(_yaml(slug), encoding="utf-8")
            (sources / "denylist.yml").write_text("boards: []\n", encoding="utf-8")
            report = run(sources, data, now=NOW, fetch=fetch, sleep=waits.append)
            shard = json.loads((data / "shards" / "greenhouse" / "acme.json").read_text(encoding="utf-8"))
        self.assertEqual(waits, [1])
        self.assertTrue(report["publish"])
        self.assertEqual(report["jobs"], 2)
        self.assertEqual(shard["jobs"][0]["id"], "acme")
        self.assertNotIn("description", shard["jobs"][0])

    def test_index_off_and_a_sharp_drop_are_honored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources"
            sources.mkdir()
            data = root / "data"
            (sources / "acme.yml").write_text(_yaml("acme"), encoding="utf-8")
            (sources / "denylist.yml").write_text("boards: []\n", encoding="utf-8")
            company = root / "companies" / "a"
            company.mkdir(parents=True)
            (company / "acme.md").write_text("---\nslug: acme\nindex: off\n---\n\nAcme.\n", encoding="utf-8")
            calls = []
            report = run(
                sources,
                data,
                now=NOW,
                fetch=lambda source, etag: calls.append(source) or {"ok": True, "jobs": []},
                sleep=lambda _seconds: None,
                root=root,
            )
            self.assertEqual(calls, [])
            self.assertEqual(report["companies"], 0)

            # A published snapshot of 20 jobs, then a fetch that returns none.
            (sources / "beta.yml").write_text(_yaml("beta"), encoding="utf-8")
            prior = data / "shards" / "greenhouse"
            prior.mkdir(parents=True)
            (prior / "beta.json").write_text(
                json.dumps(
                    {
                        "ats": "greenhouse",
                        "board": "beta",
                        "slug": "beta",
                        "status": "ok",
                        "checked_at": "2026-11-14T06:00:00Z",
                        "failed_at": None,
                        "jobs": [_job(str(number)) for number in range(20)],
                    }
                ),
                encoding="utf-8",
            )
            report = run(
                sources,
                data,
                now=NOW,
                fetch=lambda source, etag: {"ok": True, "jobs": []},
                sleep=lambda _seconds: None,
                root=root,
            )
            kept = json.loads((prior / "beta.json").read_text(encoding="utf-8"))
        self.assertFalse(report["publish"])
        self.assertEqual(report["dropped"], ["greenhouse"])
        self.assertEqual(len(kept["jobs"]), 20)


def _yaml(slug: str) -> str:
    source = _source(slug)
    return (
        f"slug: {source['slug']}\nname: {source['name']}\nwebsite: {source['website']}\n"
        f"ats: {source['ats']}\nboard: {source['board']}\n"
    )


if __name__ == "__main__":
    unittest.main()
