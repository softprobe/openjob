"""Schema errors, llms.txt, and the one-post guard."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from validator.posts import validate_post
from validator.pr import check_pr
from validator.publish import write_discovery

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 13)
ORIGIN = "https://softprobe.github.io/openjob"


class SchemaErrorTests(unittest.TestCase):
    def test_a_missing_field_names_the_fix_and_the_schema(self) -> None:
        root = _tree({"jobs/2026/11/acme-backend-engineer.md": _job(drop="location")})
        try:
            issues = validate_post(
                root=root,
                rel="jobs/2026/11/acme-backend-engineer.md",
                today=TODAY,
                author="ada",
                new_file=True,
            )
        finally:
            shutil.rmtree(root)
        schema = [issue for issue in issues if issue.code == "schema" and "location" in issue.message]
        self.assertTrue(schema, [issue.message for issue in issues])
        message = schema[0].message
        self.assertIn("jobs/2026/11/acme-backend-engineer.md", message)
        self.assertIn("field `location` is missing", message)
        self.assertIn("location: Remote", schema[0].fix)
        self.assertIn(f"{ORIGIN}/schema/job.json", schema[0].fix)

    def test_existing_repository_posts_still_pass(self) -> None:
        from validator.posts import validate_tree

        issues = validate_tree(ROOT, today=TODAY)
        self.assertEqual(issues, [], [f"{issue.path}: {issue.message}" for issue in issues])


class DiscoveryTests(unittest.TestCase):
    def test_llms_txt_and_schemas_are_in_the_build(self) -> None:
        site = Path(tempfile.mkdtemp())
        try:
            write_discovery(site, {"generated": "2026-11-13T00:00:00Z", "posts": []})
            llms = (site / "llms.txt").read_text(encoding="utf-8")
            full = (site / "llms-full.txt").read_text(encoding="utf-8")
            job = json.loads((site / "schema" / "job.json").read_text(encoding="utf-8"))
            talent = json.loads((site / "schema" / "talent.json").read_text(encoding="utf-8"))
            company = json.loads((site / "schema" / "company.json").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(site)
        self.assertTrue(llms.startswith("# OpenJob\n"))
        self.assertIn("https://raw.githubusercontent.com/softprobe/openjob/main/AGENTS.md", llms)
        self.assertIn(f"{ORIGIN}/schema/job.json", llms)
        self.assertIn(f"{ORIGIN}/schema/talent.json", llms)
        self.assertIn(f"{ORIGIN}/schema/company.json", llms)
        self.assertIn("https://github.com/softprobe/openjob/new/main/jobs", llms)
        self.assertIn("https://github.com/softprobe/openjob/new/main/talents", llms)
        self.assertIn("https://github.com/softprobe/openjob/new/main/companies", llms)
        self.assertIn("Add one new post per pull request.", full)
        self.assertIn("## FAQ", full)
        self.assertEqual(job["title"], "Job")
        self.assertEqual(job["$id"], f"{ORIGIN}/schema/job.json")
        self.assertEqual(talent["$id"], f"{ORIGIN}/schema/talent.json")
        self.assertEqual(company["$id"], f"{ORIGIN}/schema/company.json")
        self.assertIn("common.json#/$defs/slug", json.dumps(job))
        self.assertTrue((ROOT / "site" / "index.html").read_text(encoding="utf-8").find("Use your AI agent") > 0)


class GuardTests(unittest.TestCase):
    def test_a_repeated_title_is_flagged(self) -> None:
        first = "jobs/2026/11/acme-backend-engineer.md"
        # The second file uses another slug and the same title, so the path is valid
        # and the duplicate rule is what rejects it.
        head = _tree(
            {
                first: _job(),
                "jobs/2026/12/acme-staff-engineer.md": _job(
                    title="Backend engineer",
                    role_slug="staff-engineer",
                    posted="2026-12-01",
                ),
            }
        )
        base = _tree({first: _job()})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        duplicates = [issue for issue in result.issues if issue.code == "duplicate"]
        self.assertEqual(len(duplicates), 1)
        self.assertIn("already exist", duplicates[0].message)
        self.assertIn(first, duplicates[0].message)
        self.assertFalse(result.automerge)


def _job(**extra: object) -> str:
    drop = extra.pop("drop", None)
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
    if drop:
        meta.pop(str(drop), None)
    body = "Describe the work, the team, and the location without a phone number or an email address.\n"
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


def _tree(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root
