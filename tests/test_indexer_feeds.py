"""Feed parsers keep facts and drop descriptions. Sources skip the denylist."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from indexer.feeds import parse
from indexer.sources import load_sources

_DESCRIPTION = "This full description must never be stored. Call the office at 555-0100."


class FeedTests(unittest.TestCase):
    def test_greenhouse_keeps_facts_and_drops_the_description(self) -> None:
        payload = json.dumps(
            {
                "jobs": [
                    {
                        "id": 7,
                        "title": "Research engineer",
                        "company_name": "Anthropic",
                        "absolute_url": "https://boards.greenhouse.io/anthropic/jobs/7",
                        "updated_at": "2026-11-02T00:00:00Z",
                        "first_published": "2026-11-01T00:00:00Z",
                        "location": {"name": "Remote - US"},
                        "departments": [{"name": "Research"}],
                        "content": _DESCRIPTION,
                        "metadata": [{"name": "Salary", "value": "200000-300000 USD"}],
                    }
                ]
            }
        ).encode()
        jobs = parse("greenhouse", payload, company="Anthropic")
        self.assertEqual(len(jobs), 1)
        job = jobs[0].as_dict()
        self.assertEqual(job["id"], "7")
        self.assertEqual(job["remote"], "remote")
        self.assertEqual(job["department"], "Research")
        self.assertEqual(job["posted"], "2026-11-01")
        self.assertEqual(job["salary_text"], "200000-300000 USD")
        self.assertEqual(job["salary_source"], "greenhouse")
        self.assertNotIn("content", job)
        self.assertNotIn(_DESCRIPTION, json.dumps(job))

    def test_lever_drops_description_fields(self) -> None:
        payload = json.dumps(
            [
                {
                    "id": "abc",
                    "text": "Backend engineer",
                    "categories": {"location": "London", "team": "Platform", "commitment": "Full-time"},
                    "workplaceType": "hybrid",
                    "hostedUrl": "https://jobs.lever.co/acme/abc",
                    "applyUrl": "https://jobs.lever.co/acme/abc/apply",
                    "createdAt": 1761955200000,
                    "description": _DESCRIPTION,
                    "descriptionPlain": _DESCRIPTION,
                    "salaryRange": {"min": 100000, "max": 140000, "currency": "GBP", "interval": "year"},
                }
            ]
        ).encode()
        job = parse("lever", payload, company="Acme")[0].as_dict()
        self.assertEqual(job["title"], "Backend engineer")
        self.assertEqual(job["remote"], "hybrid")
        self.assertEqual(job["employment_type"], "FULL_TIME")
        self.assertEqual(job["salary_source"], "lever")
        self.assertIn("100000-140000 GBP", job["salary_text"])
        self.assertNotIn(_DESCRIPTION, json.dumps(job))

    def test_ashby_skips_unlisted_jobs_and_keeps_the_salary_summary(self) -> None:
        payload = json.dumps(
            {
                "jobs": [
                    {
                        "id": "listed",
                        "title": "Member of technical staff",
                        "location": "San Francisco",
                        "department": "Research",
                        "workplaceType": "OnSite",
                        "employmentType": "FullTime",
                        "isListed": True,
                        "publishedAt": "2026-10-01T12:00:00.000Z",
                        "jobUrl": "https://jobs.ashbyhq.com/openai/listed",
                        "applyUrl": "https://jobs.ashbyhq.com/openai/listed/apply",
                        "descriptionHtml": _DESCRIPTION,
                        "compensation": {"scrapeableCompensationSalarySummary": "$200k – $300k"},
                    },
                    {
                        "id": "hidden",
                        "title": "Direct only",
                        "isListed": False,
                        "jobUrl": "https://jobs.ashbyhq.com/openai/hidden",
                    },
                ]
            }
        ).encode()
        jobs = parse("ashby", payload, company="OpenAI")
        self.assertEqual([job.id for job in jobs], ["listed"])
        self.assertEqual(jobs[0].remote, "onsite")
        self.assertEqual(jobs[0].salary_text, "$200k – $300k")
        self.assertNotIn(_DESCRIPTION, json.dumps(jobs[0].as_dict()))

    def test_workable_reads_the_widget_fields(self) -> None:
        payload = json.dumps(
            {
                "name": "Hugging Face",
                "jobs": [
                    {
                        "title": "Machine learning engineer",
                        "shortcode": "HF1",
                        "url": "https://apply.workable.com/huggingface/j/HF1",
                        "application_url": "https://apply.workable.com/huggingface/j/HF1/apply",
                        "employment_type": "Full-time",
                        "telecommuting": True,
                        "department": "Research",
                        "city": "Paris",
                        "country": "France",
                        "published_on": "2026-09-01",
                        "description": _DESCRIPTION,
                    }
                ],
            }
        ).encode()
        job = parse("workable", payload, company="Hugging Face")[0]
        self.assertEqual(job.company, "Hugging Face")
        self.assertEqual(job.remote, "remote")
        self.assertEqual(job.location, "Paris, France")
        self.assertEqual(job.employment_type, "FULL_TIME")
        self.assertNotIn(_DESCRIPTION, json.dumps(job.as_dict()))


class SourceListTests(unittest.TestCase):
    def test_a_denied_board_is_not_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "acme.yml").write_text(
                "slug: acme\nname: Acme\nwebsite: https://acme.example\nats: greenhouse\nboard: acme\n",
                encoding="utf-8",
            )
            (root / "beta.yml").write_text(
                "slug: beta\nname: Beta\nwebsite: https://beta.example\nats: lever\nboard: beta\n",
                encoding="utf-8",
            )
            (root / "denylist.yml").write_text(
                "boards:\n  - ats: greenhouse\n    board: acme\n",
                encoding="utf-8",
            )
            loaded = load_sources(root)
        self.assertEqual([item["slug"] for item in loaded], ["beta"])


if __name__ == "__main__":
    unittest.main()
