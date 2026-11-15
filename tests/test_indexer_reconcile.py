"""A missing job closes, a failed feed stays stale, and a sharp drop is reported."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from indexer.reconcile import platform_drop, reconcile, visible

NOW = datetime(2026, 11, 15, 6, 0, tzinfo=timezone.utc)


def _job(job_id: str, title: str = "Engineer") -> dict:
    return {
        "id": job_id,
        "title": title,
        "company": "Acme",
        "location": "Remote",
        "remote": "remote",
        "department": "",
        "employment_type": "",
        "salary_text": "",
        "salary_source": "",
        "posted": "2026-11-01",
        "updated": "",
        "deadline": "",
        "source_url": f"https://boards.example/{job_id}",
        "apply_url": f"https://boards.example/{job_id}",
    }


class ReconcileTests(unittest.TestCase):
    def test_a_missing_job_is_closed_on_the_first_successful_fetch(self) -> None:
        previous = reconcile(None, {"ok": True, "jobs": [_job("a"), _job("b")], "etag": "1"}, NOW)
        nxt = reconcile(previous, {"ok": True, "jobs": [_job("b", "Staff engineer")], "etag": "2"}, NOW)
        self.assertEqual([job["id"] for job in nxt["jobs"]], ["b"])
        self.assertEqual(nxt["jobs"][0]["title"], "Staff engineer")
        self.assertEqual(nxt["jobs"][0]["first_seen"], previous["jobs"][1]["first_seen"])
        self.assertEqual(nxt["status"], "ok")

    def test_a_failed_fetch_keeps_the_snapshot_and_hides_it_after_48_hours(self) -> None:
        previous = reconcile(None, {"ok": True, "jobs": [_job("a")], "etag": "1"}, NOW)
        failed = reconcile(previous, {"ok": False}, NOW + timedelta(hours=1))
        self.assertEqual(failed["status"], "stale")
        self.assertEqual(failed["jobs"], previous["jobs"])
        self.assertTrue(visible(failed, NOW + timedelta(hours=47)))
        self.assertFalse(visible(failed, NOW + timedelta(hours=49)))

    def test_a_later_success_clears_the_stale_flag(self) -> None:
        previous = reconcile(None, {"ok": True, "jobs": [_job("a")], "etag": "1"}, NOW)
        failed = reconcile(previous, {"ok": False}, NOW + timedelta(hours=1))
        restored = reconcile(failed, {"ok": True, "jobs": [_job("a")], "etag": "3"}, NOW + timedelta(hours=2))
        self.assertEqual(restored["status"], "ok")
        self.assertIsNone(restored["failed_at"])
        self.assertTrue(visible(restored, NOW + timedelta(days=3)))

    def test_a_sharp_platform_drop_is_named(self) -> None:
        self.assertEqual(platform_drop({"greenhouse": 100, "lever": 10}, {"greenhouse": 40, "lever": 1}), ["greenhouse"])
        self.assertEqual(platform_drop({"ashby": 100}, {"ashby": 80}), [])


if __name__ == "__main__":
    unittest.main()
