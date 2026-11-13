"""Schema, path, size, and binary rejection."""

from __future__ import annotations

import json
import shutil
import unittest
from datetime import date
from pathlib import Path

import yaml
from jsonschema.validators import Draft202012Validator

from samples import sample_tree
from validator.posts import binary_issues, validate_post, validate_tree

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 11, 13)


def codes(issues: list) -> set[str]:
    return {issue.code for issue in issues}


class FixtureRejectionTests(unittest.TestCase):
    def test_rejects_bad_path(self) -> None:
        issues = validate_post(root=FIXTURES / "bad-path", rel="jobs/nope.md", today=TODAY)
        self.assertIn("bad-path", codes(issues))
        self.assertNotIn("schema", codes(issues))
        self.assertTrue(any("jobs/YYYY/MM" in issue.message for issue in issues))

    def test_rejects_oversize_file(self) -> None:
        root = FIXTURES / "oversize"
        rel = "jobs/2026/11/example-studio-open-source-maintainer.md"
        self.assertGreater((root / rel).stat().st_size, 10 * 1024)
        issues = validate_post(root=root, rel=rel, today=TODAY)
        self.assertEqual(codes(issues), {"oversize"})
        self.assertIn("10240", issues[0].message)

    def test_rejects_pdf_and_png(self) -> None:
        pdf = binary_issues(FIXTURES / "binary" / "resume.pdf", "resume.pdf")
        png = binary_issues(FIXTURES / "binary" / "avatar.png", "avatar.png")
        self.assertEqual(codes(pdf), {"binary"})
        self.assertEqual(codes(png), {"binary"})
        self.assertIn("pdf", pdf[0].message)
        self.assertIn(".png", png[0].message)


class SchemaTests(unittest.TestCase):
    def test_schemas_are_well_formed(self) -> None:
        for path in sorted((ROOT / "schema").glob("*.json")):
            with self.subTest(path=path.name):
                Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

    def test_rejects_email_field(self) -> None:
        text = _job(email="ada@gmail.com")
        path = "jobs/2026/11/acme-backend-engineer.md"
        root = _write({path: text})
        try:
            issues = validate_post(
                root=root,
                rel=path,
                today=TODAY,
                author="ada",
                maintainers={"zwobill"},
                new_file=True,
            )
        finally:
            _cleanup(root)
        self.assertIn("schema", codes(issues))
        self.assertIn("privacy-email", codes(issues))

    def test_seed_posts_are_valid(self) -> None:
        root = sample_tree()
        try:
            issues = validate_tree(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [f"{issue.path}: {issue.message}" for issue in issues])


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
    import tempfile

    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def _cleanup(root: Path) -> None:
    import shutil

    shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
