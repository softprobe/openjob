"""Index projection and expiry selection."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from samples import SAMPLES, sample_tree
from validator.expire import select_expired
from validator.index import build_index

ROOT = Path(__file__).resolve().parents[1]
FEDERATED = Path(__file__).resolve().parent / "fixtures" / "federated"
TODAY = date(2026, 11, 13)


class IndexTests(unittest.TestCase):
    def test_repository_index_skips_tests_templates_and_samples(self) -> None:
        document = build_index(ROOT, today=TODAY)
        paths = {post["path"] for post in document["posts"]}
        self.assertIn("companies/s/softprobe.md", paths)
        self.assertIn("jobs/2026/11/softprobe-software-engineer.md", paths)
        for path in paths:
            top = path.split("/", 1)[0]
            self.assertIn(top, {"jobs", "talents", "companies"})
            self.assertNotIn(top, {"tests", "templates"})
        self.assertNotIn("jobs/2026/11/example-studio-open-source-maintainer.md", paths)
        self.assertNotIn("talents/z/zwobill.md", paths)
        self.assertNotIn("companies/e/example-studio.md", paths)
        self.assertTrue((ROOT / "templates" / "job.md").is_file())
        for rel in SAMPLES:
            self.assertTrue((ROOT / "tests" / "fixtures" / "samples" / rel).is_file())
            self.assertFalse((ROOT / rel).exists())

    def test_fixtures_beside_a_post_are_not_indexed(self) -> None:
        root = Path(tempfile.mkdtemp())
        try:
            _write(root, "jobs/2026/11/acme-backend-engineer.md", _job())
            _write(root, "tests/fixtures/samples/jobs/2026/11/acme-backend-engineer.md", _job())
            _write(root, "templates/job.md", _job())
            _write(root, "tests/jobs/2026/11/hidden-role.md", _job(role_slug="hidden-role", title="Hidden role"))
            document = build_index(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertEqual(
            [post["path"] for post in document["posts"]],
            ["jobs/2026/11/acme-backend-engineer.md"],
        )

    def test_seed_index_includes_samples(self) -> None:
        root = sample_tree()
        try:
            document = build_index(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertEqual({post["path"] for post in document["posts"]}, set(SAMPLES))
        kinds = {post["kind"] for post in document["posts"]}
        self.assertEqual(kinds, {"job", "talent", "company"})
        self.assertTrue(all(post["example"] for post in document["posts"]))
        self.assertTrue(all(post["expires"] is None for post in document["posts"]))

    def test_a_real_post_does_not_change_the_sample_index(self) -> None:
        root = sample_tree()
        try:
            extra = root / "companies" / "n" / "northwind.md"
            extra.parent.mkdir(parents=True)
            text = (root / "companies/e/example-studio.md").read_text(encoding="utf-8")
            text = text.replace("slug: example-studio", "slug: northwind")
            text = text.replace("name: Example Studio", "name: Northwind")
            text = text.replace("example: true", "example: false")
            extra.write_text(text, encoding="utf-8")
            document = build_index(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        by_path = {post["path"]: post for post in document["posts"]}
        self.assertEqual(len(by_path), 4)
        self.assertFalse(by_path["companies/n/northwind.md"]["example"])
        for rel in SAMPLES:
            self.assertTrue(by_path[rel]["example"])
            self.assertIsNone(by_path[rel]["expires"])

    def test_federated_profile_is_indexed(self) -> None:
        document = build_index(FEDERATED, today=TODAY)
        self.assertEqual(len(document["posts"]), 1)
        post = document["posts"][0]
        self.assertEqual(post["kind"], "talent-ref")
        self.assertTrue(post["federated"])
        self.assertEqual(post["profile_url"], "https://github.com/ada/openjob-profile")
        self.assertEqual(post["owner"], "ada")


class ExpiryTests(unittest.TestCase):
    def test_jobs_talents_and_samples(self) -> None:
        root = Path(tempfile.mkdtemp())
        try:
            _write(
                root,
                "jobs/2026/01/acme-old-role.md",
                _job(posted="2026-01-01", role_slug="old-role", title="Old role"),
            )
            _write(root, "jobs/2026/11/acme-backend-engineer.md", _job())
            _write(
                root,
                "jobs/2026/01/acme-sample-role.md",
                _job(role_slug="sample-role", title="Sample role", example=True, posted="2026-01-01"),
            )
            _write(root, "talents/a/ada.md", _talent(posted="2025-01-01"))
            _write(
                root,
                "talents/a/ada-new.md",
                _talent(github="ada-new", name="Ada New", posted="2026-08-01"),
            )
            _write(
                root,
                "talents/r/renewed-person.md",
                _talent(
                    github="renewed-person",
                    name="Renewed",
                    posted="2025-01-01",
                    renewed="2026-11-01",
                ),
            )
            _write(root, "companies/a/acme.md", _company())
            expired = {item.path for item in select_expired(root, today=TODAY)}
        finally:
            shutil.rmtree(root)
        self.assertIn("jobs/2026/01/acme-old-role.md", expired)
        self.assertIn("talents/a/ada.md", expired)
        self.assertNotIn("jobs/2026/11/acme-backend-engineer.md", expired)
        self.assertNotIn("jobs/2026/01/acme-sample-role.md", expired)
        self.assertNotIn("talents/a/ada-new.md", expired)
        self.assertNotIn("talents/r/renewed-person.md", expired)
        self.assertNotIn("companies/a/acme.md", expired)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _dump(meta: dict[str, object]) -> str:
    body = "Describe the work, the team, and the location without a phone number or an email address.\n"
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


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
    return _dump(meta)


def _talent(**extra: object) -> str:
    meta: dict[str, object] = {
        "kind": "talent",
        "name": "Ada Lovelace",
        "github": "ada",
        "headline": "Engineer who ships compilers",
        "location": "Example City",
        "remote": True,
        "languages": ["en"],
        "tags": ["compilers"],
        "open_to": ["contract"],
        "website": "https://example.com",
        "posted": "2026-11-13",
    }
    meta.update(extra)
    return _dump(meta)


def _company() -> str:
    meta: dict[str, object] = {
        "kind": "company",
        "slug": "acme",
        "name": "Acme",
        "website": "https://example.com",
        "location": "Example City",
        "tags": ["sample"],
        "posted": "2026-11-13",
        "posted_by": "ada",
    }
    return _dump(meta)


if __name__ == "__main__":
    unittest.main()
