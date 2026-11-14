"""Structured job fields, the share image, and a configurable Pages origin."""

from __future__ import annotations

import base64
import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from validator.index import build_index, write_pages
from validator.jsonld import job_posting
from validator.posts import binary_issues, validate_post
from validator.publish import write_discovery
from validator.share import (
    GOOGLE_SITE_VERIFICATION,
    GOOGLE_VERIFICATION_BODY,
    GOOGLE_VERIFICATION_FILE,
    permalink,
    render_share_comment,
)

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 13)
JOB = "jobs/2026/11/acme-backend-engineer.md"


class StructuredJobTests(unittest.TestCase):
    def test_fields_render_and_become_jobposting(self) -> None:
        root = _write(
            {
                JOB: _job(
                    remote="onsite",
                    employment_type=["FULL_TIME", "CONTRACTOR"],
                    salary={"min": 100000, "max": 140000, "currency": "USD", "unit": "YEAR"},
                    locations=[
                        {"city": "Los Altos", "region": "CA", "country": "US"},
                        {"city": "Shanghai", "country": "CN"},
                    ],
                    location="Somewhere else",
                )
            }
        )
        site = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True), [])
            document = build_index(root, today=TODAY)
            post = document["posts"][0]
            self.assertEqual(post["remote"], "onsite")
            self.assertEqual(post["employment_type"], ["FULL_TIME", "CONTRACTOR"])
            self.assertEqual(post["salary"]["currency"], "USD")
            self.assertEqual(post["locations"][1], {"city": "Shanghai", "country": "CN"})
            posting = job_posting(post, "<p>Role</p>")
            self.assertEqual(posting["employmentType"], ["FULL_TIME", "CONTRACTOR"])
            self.assertEqual(posting["baseSalary"]["currency"], "USD")
            self.assertEqual(posting["baseSalary"]["value"]["minValue"], 100000)
            self.assertEqual(posting["baseSalary"]["value"]["maxValue"], 140000)
            self.assertEqual(posting["baseSalary"]["value"]["unitText"], "YEAR")
            self.assertEqual(
                [item["address"]["addressLocality"] for item in posting["jobLocation"]],
                ["Los Altos", "Shanghai"],
            )
            self.assertNotIn("jobLocationType", posting)
            write_pages(root, site, document)
            page = (site / "p" / JOB[:-3] / "index.html").read_text(encoding="utf-8")
            self.assertIn("Full-time", page)
            self.assertIn("Contractor", page)
            self.assertIn("USD 100000–140000 / year", page)
            self.assertIn("Los Altos, CA, US", page)
            self.assertIn("Shanghai, CN", page)
            self.assertIn('property="og:image"', page)
            self.assertIn('content="summary_large_image"', page)
            self.assertIn('name="google-site-verification"', page)
            self.assertNotIn('name="msvalidate.01"', page)
        finally:
            shutil.rmtree(root)
            shutil.rmtree(site)

    def test_free_text_location_remains_when_locations_are_absent(self) -> None:
        posting = job_posting(
            {
                "title": "Engineer",
                "path": "jobs/2026/11/acme.md",
                "permalink": "https://softprobe.github.io/openjob/p/jobs/2026/11/acme/",
                "posted": "2026-11-13",
                "location": "Los Altos, CA / Shanghai",
                "remote": "hybrid",
                "employment_type": None,
                "salary": None,
                "locations": None,
            },
            "<p>Role</p>",
        )
        self.assertNotIn("employmentType", posting)
        self.assertNotIn("baseSalary", posting)
        self.assertEqual([item["address"]["addressCountry"] for item in posting["jobLocation"]], ["US", "CN"])

    def test_remote_uses_structured_countries_and_a_single_salary(self) -> None:
        posting = job_posting(
            {
                "title": "Engineer",
                "location": "Example City",
                "remote": "remote",
                "employment_type": "FULL_TIME",
                "salary": {"min": 80, "currency": "USD", "unit": "HOUR"},
                "locations": [{"country": "US"}],
            },
            "<p>Role</p>",
        )
        self.assertEqual(posting["employmentType"], ["FULL_TIME"])
        self.assertEqual(posting["baseSalary"]["value"]["value"], 80)
        self.assertNotIn("minValue", posting["baseSalary"]["value"])
        self.assertEqual(posting["jobLocationType"], "TELECOMMUTE")
        self.assertEqual(posting["applicantLocationRequirements"]["name"], "United States")
        self.assertNotIn("jobLocation", posting)

    def test_rejects_unknown_codes_and_an_inverted_salary(self) -> None:
        root = _write({JOB: _job(salary={"min": 10, "max": 4, "currency": "ZZZ", "unit": "HOUR"})})
        try:
            messages = " ".join(
                issue.message for issue in validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
            )
        finally:
            shutil.rmtree(root)
        self.assertIn("max is less than min", messages)
        self.assertIn("ZZZ", messages)
        root = _write({JOB: _job(locations=[{"country": "ZZ"}])})
        try:
            messages = " ".join(
                issue.message for issue in validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
            )
        finally:
            shutil.rmtree(root)
        self.assertIn("ZZ", messages)
        self.assertIn("ISO 3166-1", messages)

    def test_softprobe_places_match_the_post_and_invent_nothing_else(self) -> None:
        text = (ROOT / "jobs/2026/11/softprobe-software-engineer.md").read_text(encoding="utf-8")
        front = text.split("---", 2)[1]
        self.assertIn('location: "Los Altos, CA / Shanghai"', front)
        self.assertIn("remote: hybrid", front)
        self.assertIn("city: Los Altos", front)
        self.assertIn("region: CA", front)
        self.assertIn("country: US", front)
        self.assertIn("city: Shanghai", front)
        self.assertIn("country: CN", front)
        self.assertNotIn("salary:", front)
        self.assertNotIn("employment_type:", front)


class OriginAndVerificationTests(unittest.TestCase):
    def test_share_image_is_1200_by_630(self) -> None:
        source = ROOT / "site" / "og.png.b64"
        self.assertEqual(binary_issues(source, "site/og.png.b64"), [])
        data = base64.b64decode("".join(source.read_text(encoding="ascii").split()), validate=True)
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(int.from_bytes(data[16:20], "big"), 1200)
        self.assertEqual(int.from_bytes(data[20:24], "big"), 630)
        site = Path(tempfile.mkdtemp())
        try:
            write_discovery(site, {"generated": "2026-11-13T00:00:00Z", "posts": []})
            self.assertEqual((site / "og.png").read_bytes(), data)
        finally:
            shutil.rmtree(site)

    def test_default_origin_has_no_cname_and_keeps_the_google_token(self) -> None:
        site = Path(tempfile.mkdtemp())
        try:
            write_discovery(site, {"generated": "2026-11-13T00:00:00Z", "posts": []})
            home = (site / "index.html").read_text(encoding="utf-8")
            about = (site / "about" / "index.html").read_text(encoding="utf-8")
            self.assertIn("https://softprobe.github.io/openjob/og.png", home)
            self.assertIn(f'content="{GOOGLE_SITE_VERIFICATION}"', home)
            self.assertIn(f'content="{GOOGLE_SITE_VERIFICATION}"', about)
            self.assertNotIn('name="msvalidate.01"', home)
            self.assertFalse((site / "CNAME").exists())
            self.assertIn("github.io project site", (site / "robots.txt").read_text(encoding="utf-8"))
            body = (site / GOOGLE_VERIFICATION_FILE).read_text(encoding="utf-8")
            self.assertEqual(body, GOOGLE_VERIFICATION_BODY)
            self.assertEqual((ROOT / "site" / GOOGLE_VERIFICATION_FILE).read_text(encoding="utf-8"), body)
        finally:
            shutil.rmtree(site)

    def test_custom_origin_writes_cname_and_verification_overrides(self) -> None:
        site = Path(tempfile.mkdtemp())
        previous = {key: os.environ.get(key) for key in ("PAGES_ORIGIN", "GOOGLE_SITE_VERIFICATION", "BING_SITE_VERIFICATION")}
        os.environ["PAGES_ORIGIN"] = "https://jobs.example.com/"
        os.environ["GOOGLE_SITE_VERIFICATION"] = "custom-google-token"
        os.environ["BING_SITE_VERIFICATION"] = "custom-bing-token"
        try:
            write_discovery(
                site,
                {
                    "generated": "2026-11-13T00:00:00Z",
                    "posts": [
                        {
                            "kind": "job",
                            "path": JOB,
                            "title": "Backend engineer",
                            "org": "Acme",
                            "permalink": permalink(JOB),
                            "posted": "2026-11-13",
                            "excerpt": "A public excerpt for the feed.",
                        }
                    ],
                },
            )
            self.assertEqual((site / "CNAME").read_text(encoding="utf-8"), "jobs.example.com\n")
            self.assertEqual(permalink(JOB), "https://jobs.example.com/p/jobs/2026/11/acme-backend-engineer/")
            home = (site / "index.html").read_text(encoding="utf-8")
            archive = (site / "jobs" / "page" / "1" / "index.html").read_text(encoding="utf-8")
            robots = (site / "robots.txt").read_text(encoding="utf-8")
            self.assertIn('rel="canonical" href="https://jobs.example.com/"', home)
            self.assertIn("https://jobs.example.com/og.png", home)
            self.assertIn('content="custom-google-token"', home)
            self.assertIn('name="msvalidate.01" content="custom-bing-token"', home)
            self.assertIn("https://jobs.example.com/jobs/page/1/", archive)
            self.assertIn('property="og:image"', archive)
            self.assertIn("served at the host root", robots)
            self.assertIn("Sitemap: https://jobs.example.com/sitemap.xml", robots)
            comment = render_share_comment(
                {"kind": "job", "title": "Backend engineer", "company_name": "Acme", "location": "Example City"},
                JOB,
            )
            self.assertIn("https://jobs.example.com/p/jobs/2026/11/acme-backend-engineer/", comment)
            self.assertIn("https%3A%2F%2Fjobs.example.com%2Fp%2F", comment)
        finally:
            shutil.rmtree(site)
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_project_site_origin_does_not_write_cname(self) -> None:
        site = Path(tempfile.mkdtemp())
        previous = os.environ.get("PAGES_ORIGIN")
        os.environ["PAGES_ORIGIN"] = "https://softprobe.github.io/openjob"
        try:
            write_discovery(site, {"generated": "2026-11-13T00:00:00Z", "posts": []})
            self.assertFalse((site / "CNAME").exists())
        finally:
            shutil.rmtree(site)
            if previous is None:
                os.environ.pop("PAGES_ORIGIN", None)
            else:
                os.environ["PAGES_ORIGIN"] = previous

    def test_bad_pages_origin_is_rejected(self) -> None:
        previous = os.environ.get("PAGES_ORIGIN")
        os.environ["PAGES_ORIGIN"] = "http://jobs.example.com"
        try:
            with self.assertRaises(ValueError):
                permalink(JOB)
        finally:
            if previous is None:
                os.environ.pop("PAGES_ORIGIN", None)
            else:
                os.environ["PAGES_ORIGIN"] = previous


def _job(**extra: object) -> str:
    meta: dict[str, object] = {
        "kind": "job",
        "title": "Backend engineer",
        "company": "acme",
        "company_name": "Acme",
        "role_slug": "backend-engineer",
        "location": "Example City",
        "remote": True,
        "languages": ["en"],
        "tags": ["backend"],
        "apply": "https://example.com/jobs/backend-engineer",
        "posted": "2026-11-13",
        "posted_by": "ada",
    }
    meta.update(extra)
    body = "Describe the work, the team, and the location without a phone number or an email address.\n"
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


def _write(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


if __name__ == "__main__":
    unittest.main()
