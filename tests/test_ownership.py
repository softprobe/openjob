"""GitHub-login ownership for profiles, companies, and jobs."""

from __future__ import annotations

import shutil
import unittest
from datetime import date
from pathlib import Path

import yaml

from validator.posts import validate_tree
from validator.pr import check_pr

TODAY = date(2026, 11, 14)
ROOT = Path(__file__).resolve().parents[1]


class TalentOwnershipTests(unittest.TestCase):
    def test_author_can_add_and_delete_their_profile(self) -> None:
        added = _check({"talents/ada.md": _talent()}, {}, "ada")
        self.assertEqual(added.issues, [], _text(added))
        self.assertTrue(added.automerge)
        base = {"talents/ada.md": _talent()}
        deleted = _check({}, base, "ada")
        self.assertEqual(deleted.issues, [], _text(deleted))
        self.assertTrue(deleted.automerge)

    def test_login_match_is_case_insensitive(self) -> None:
        result = _check({"talents/Ada.md": _talent(github="Ada")}, {}, "ada")
        self.assertEqual(result.issues, [], _text(result))
        self.assertTrue(result.automerge)

    def test_a_letter_folder_is_rejected(self) -> None:
        result = _check({"talents/a/ada.md": _talent()}, {}, "ada")
        self.assertTrue(any(issue.code == "bad-path" for issue in result.issues))
        self.assertTrue(any("talents/ada.md" in issue.message for issue in result.issues))
        self.assertFalse(result.automerge)

    def test_someone_else_cannot_add_edit_or_delete_a_profile(self) -> None:
        added = _check({"talents/ada.md": _talent()}, {}, "mallory")
        edited = _check(
            {"talents/ada.md": _talent(headline="Still Ada")},
            {"talents/ada.md": _talent()},
            "mallory",
        )
        deleted = _check({}, {"talents/ada.md": _talent()}, "mallory")
        for result in (added, edited, deleted):
            self.assertTrue(any(issue.code == "ownership" for issue in result.issues), _text(result))
            self.assertFalse(result.automerge)
            self.assertTrue(any("talents/mallory.md" in issue.message or "belongs to" in issue.message for issue in result.issues))


class CompanyOwnershipTests(unittest.TestCase):
    def test_a_new_company_needs_the_author_in_owners_and_does_not_automerge(self) -> None:
        ok = _check({"companies/a/acme.md": _company()}, {}, "ada")
        self.assertEqual(ok.issues, [], _text(ok))
        self.assertFalse(ok.automerge)
        self.assertIn("reviewed once", ok.report())
        missing = _check({"companies/a/acme.md": _company(drop_owners=True)}, {}, "ada")
        self.assertTrue(any("owners" in issue.message for issue in missing.issues), _text(missing))
        outsider = _check({"companies/a/acme.md": _company(owners=["bob"])}, {}, "ada")
        self.assertTrue(any(issue.code == "ownership" for issue in outsider.issues), _text(outsider))
        self.assertFalse(outsider.automerge)

    def test_an_owner_can_edit_the_page_and_the_owner_list(self) -> None:
        original = _company()
        edited = _company(owners=["ada", "bea"], body="Acme still builds the platform and hires through its careers page.\n")
        result = _check({"companies/a/acme.md": edited}, {"companies/a/acme.md": original}, "ada")
        self.assertEqual(result.issues, [], _text(result))
        self.assertTrue(result.automerge)

    def test_someone_else_cannot_add_themselves(self) -> None:
        edited = _company(owners=["ada", "mallory"])
        result = _check({"companies/a/acme.md": edited}, {"companies/a/acme.md": _company()}, "mallory")
        self.assertTrue(any(issue.code == "ownership" for issue in result.issues), _text(result))
        self.assertFalse(result.automerge)

    def test_a_page_without_owners_still_belongs_to_posted_by_until_the_list_is_added(self) -> None:
        original = _company(slug="softprobe", drop_owners=True, posted_by="zwobill")
        migrated = _company(slug="softprobe", posted_by="zwobill", owners=["lcunsp", "zwobill"])
        allowed = _check(
            {"companies/s/softprobe.md": migrated},
            {"companies/s/softprobe.md": original},
            "zwobill",
        )
        denied = _check(
            {"companies/s/softprobe.md": migrated},
            {"companies/s/softprobe.md": original},
            "lcunsp",
        )
        self.assertEqual(allowed.issues, [], _text(allowed))
        self.assertTrue(allowed.automerge)
        self.assertTrue(any(issue.code == "ownership" for issue in denied.issues), _text(denied))
        self.assertFalse(denied.automerge)


class JobOwnershipTests(unittest.TestCase):
    def test_company_owners_can_add_and_edit_jobs(self) -> None:
        company = {"companies/a/acme.md": _company(owners=["ada", "bea"])}
        added = _check(
            {**company, "jobs/2026/11/acme-backend-engineer.md": _job(posted_by="bea")},
            company,
            "bea",
        )
        self.assertEqual(added.issues, [], _text(added))
        self.assertTrue(added.automerge)
        original = _job()
        edited = _job(body="The same role, with a clearer note about the team in Example City.\n")
        changed = _check(
            {**company, "jobs/2026/11/acme-backend-engineer.md": edited},
            {**company, "jobs/2026/11/acme-backend-engineer.md": original},
            "bea",
        )
        self.assertEqual(changed.issues, [], _text(changed))
        self.assertTrue(changed.automerge)

    def test_someone_outside_the_company_cannot_add_or_close_a_job(self) -> None:
        company = {"companies/a/acme.md": _company(owners=["ada", "bea"])}
        added = _check(
            {**company, "jobs/2026/11/acme-backend-engineer.md": _job(posted_by="mallory")},
            company,
            "mallory",
        )
        deleted = _check(company, {**company, "jobs/2026/11/acme-backend-engineer.md": _job()}, "mallory")
        for result in (added, deleted):
            self.assertTrue(any("acme" in issue.message for issue in result.issues), _text(result))
            self.assertFalse(result.automerge)

    def test_posted_by_stays_the_original_poster(self) -> None:
        company = {"companies/a/acme.md": _company(owners=["ada", "bea"])}
        edited = _job(posted_by="bea")
        result = _check(
            {**company, "jobs/2026/11/acme-backend-engineer.md": edited},
            {**company, "jobs/2026/11/acme-backend-engineer.md": _job()},
            "bea",
        )
        self.assertTrue(any("posted_by" in issue.message for issue in result.issues), _text(result))
        self.assertFalse(result.automerge)

    def test_a_job_with_no_company_page_stays_with_its_poster(self) -> None:
        added = _check({"jobs/2026/11/acme-backend-engineer.md": _job()}, {}, "ada")
        self.assertEqual(added.issues, [], _text(added))
        self.assertTrue(added.automerge)
        stolen = _check(
            {"jobs/2026/11/acme-backend-engineer.md": _job(posted_by="mallory")},
            {},
            "ada",
        )
        self.assertTrue(any(issue.code == "ownership" for issue in stolen.issues), _text(stolen))
        edited = _check(
            {"jobs/2026/11/acme-backend-engineer.md": _job(body="A longer note about the work and the team in Example City.\n")},
            {"jobs/2026/11/acme-backend-engineer.md": _job()},
            "mallory",
        )
        self.assertTrue(any("posted by `ada`" in issue.message for issue in edited.issues), _text(edited))
        self.assertFalse(edited.automerge)

    def test_the_author_argument_wins_over_a_login_written_in_the_file(self) -> None:
        result = _check({"jobs/2026/11/acme-backend-engineer.md": _job(posted_by="mallory")}, {}, "ada")
        self.assertTrue(any(issue.code == "ownership" for issue in result.issues), _text(result))
        self.assertFalse(result.automerge)


class MaintainerTests(unittest.TestCase):
    def test_a_maintainer_can_edit_but_does_not_automerge_someone_elses_post(self) -> None:
        result = _check(
            {"talents/ada.md": _talent(headline="Reviewed by a maintainer")},
            {"talents/ada.md": _talent()},
            "zwobill",
        )
        self.assertEqual(result.issues, [], _text(result))
        self.assertFalse(result.automerge)
        self.assertIn("does not own every file", result.report())

    def test_a_maintainer_who_owns_the_file_can_still_automerge(self) -> None:
        result = _check({"talents/zwobill.md": _talent(github="zwobill", name="Bill")}, {}, "zwobill")
        self.assertEqual(result.issues, [], _text(result))
        self.assertTrue(result.automerge)

    def test_the_live_company_without_owners_still_validates(self) -> None:
        issues = validate_tree(ROOT, today=TODAY)
        self.assertEqual(issues, [], [f"{issue.path}: {issue.message}" for issue in issues])


class AuthorSourceTests(unittest.TestCase):
    def test_workflows_take_the_author_from_the_pull_request_event(self) -> None:
        for name in ("automerge.yml", "validate.yml"):
            text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
            self.assertIn("PR_AUTHOR: ${{ github.event.pull_request.user.login }}", text)
            self.assertIn('--author "$PR_AUTHOR"', text)
            self.assertNotIn("posted_by", text)
            self.assertNotIn("git log", text)


def _check(head: dict[str, str], base: dict[str, str], author: str):
    head_root = _tree(head)
    base_root = _tree(base)
    try:
        return check_pr(head=head_root, base=base_root, author=author, today=TODAY)
    finally:
        shutil.rmtree(head_root)
        shutil.rmtree(base_root)


def _text(result) -> list[str]:
    return [f"{issue.code}: {issue.message}" for issue in result.issues]


def _talent(**extra: object) -> str:
    github = str(extra.pop("github", "ada"))
    meta: dict[str, object] = {
        "kind": "talent",
        "name": extra.pop("name", "Ada Lovelace"),
        "github": github,
        "headline": extra.pop("headline", "Engineer who ships compilers"),
        "location": "Example City",
        "remote": True,
        "languages": ["en"],
        "tags": ["compilers"],
        "open_to": ["contract"],
        "website": "https://example.com",
        "posted": "2026-11-14",
    }
    body = "A short public profile with a site link and no phone number or email address at all.\n"
    return _dump(meta, body)


def _company(**extra: object) -> str:
    drop_owners = bool(extra.pop("drop_owners", False))
    body = str(extra.pop("body", "Acme builds a production platform and hires through the careers page linked above.\n"))
    meta: dict[str, object] = {
        "kind": "company",
        "slug": extra.pop("slug", "acme"),
        "name": "Acme",
        "website": "https://example.com",
        "location": "Example City",
        "tags": ["backend"],
        "posted": "2026-11-14",
        "posted_by": extra.pop("posted_by", "ada"),
        "owners": extra.pop("owners", ["ada"]),
    }
    if extra.get("slug") == "softprobe" or meta["slug"] == "softprobe":
        meta["name"] = "Softprobe"
        meta["website"] = "https://www.softprobe.ai"
    meta.update(extra)
    if drop_owners:
        meta.pop("owners", None)
    if meta["slug"] == "softprobe":
        return _dump(meta, body, path_slug="softprobe")
    return _dump(meta, body)


def _job(**extra: object) -> str:
    body = str(
        extra.pop(
            "body",
            "Describe the work, the team, and the location without a phone number or an email address.\n",
        )
    )
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
        "posted": "2026-11-14",
        "posted_by": extra.pop("posted_by", "ada"),
    }
    meta.update(extra)
    return _dump(meta, body)


def _dump(meta: dict[str, object], body: str, path_slug: str | None = None) -> str:
    del path_slug
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


def _tree(files: dict[str, str]) -> Path:
    root = Path(__import__("tempfile").mkdtemp())
    for rel, content in files.items():
        if rel == "companies/s/softprobe.md":
            rel = "companies/s/softprobe.md"
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root
