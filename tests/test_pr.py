"""Pull-request scope, ownership, and auto-merge eligibility."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from validator.posts import maintainers_from
from validator.pr import check_pr

TODAY = date(2026, 11, 13)


class CheckPrTests(unittest.TestCase):
    def test_one_post_can_automerge(self) -> None:
        head = _tree({"README.md": "# openjob\n", "jobs/2026/11/acme-backend-engineer.md": _job()})
        base = _tree({"README.md": "# openjob\n"})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertEqual(result.issues, [])
        self.assertTrue(result.automerge)

    def test_several_posts_can_automerge(self) -> None:
        head = _tree(
            {
                "jobs/2026/11/acme-backend-engineer.md": _job(),
                "jobs/2026/11/acme-designer.md": _job(
                    title="Product designer",
                    role_slug="designer",
                ),
                "talents/a/ada.md": _talent(),
            }
        )
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertEqual(result.issues, [], [issue.message for issue in result.issues])
        self.assertTrue(result.automerge)
        comment = result.share_comment or ""
        self.assertIn("jobs/2026/11/acme-backend-engineer", comment)
        self.assertIn("jobs/2026/11/acme-designer", comment)
        self.assertIn("talents/a/ada", comment)

    def test_ownership_is_checked_on_each_file(self) -> None:
        head = _tree(
            {
                "jobs/2026/11/acme-backend-engineer.md": _job(),
                "jobs/2026/11/acme-designer.md": _job(
                    title="Product designer",
                    role_slug="designer",
                    posted_by="mallory",
                ),
            }
        )
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        owned = [issue for issue in result.issues if issue.code == "ownership"]
        self.assertEqual([issue.path for issue in owned], ["jobs/2026/11/acme-designer.md"])
        self.assertFalse(result.automerge)

    def test_mixed_content_and_code_needs_the_team(self) -> None:
        head = _tree(
            {
                "README.md": "# changed\n",
                "jobs/2026/11/acme-backend-engineer.md": _job(),
            }
        )
        base = _tree({"README.md": "# openjob\n"})
        docs = _tree({"README.md": "# changed\n"})
        docs_base = _tree({"README.md": "# openjob\n"})
        try:
            mixed = check_pr(head=head, base=base, author="ada", today=TODAY)
            only_docs = check_pr(head=docs, base=docs_base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
            shutil.rmtree(docs)
            shutil.rmtree(docs_base)
        for result in (mixed, only_docs):
            self.assertEqual(result.issues, [])
            self.assertFalse(result.automerge)
            report = result.report()
            self.assertIn("Softprobe team", report)
            self.assertIn("@softprobe/openjob-maintainers", report)
            self.assertIn("Auto-merge stays off", report)

    def test_maintainers_are_the_team_or_zwobill(self) -> None:
        listed = _tree(
            {
                ".github/CODEOWNERS": (
                    "* @softprobe/openjob-maintainers\n/jobs/\n/talents/\n/companies/\n"
                )
            }
        )
        missing = _tree({})
        try:
            owners = maintainers_from(listed)
            fallback = maintainers_from(missing)
        finally:
            shutil.rmtree(listed)
            shutil.rmtree(missing)
        self.assertIn("softprobe/openjob-maintainers", owners)
        self.assertIn("zwobill", owners)
        self.assertEqual(fallback, {"zwobill"})

    def test_cannot_edit_someone_elses_post(self) -> None:
        original = _talent(handle="ada")
        stolen = _talent(handle="mallory", name="Mallory")
        base = _tree({"talents/a/ada.md": original})
        head = _tree({"talents/m/mallory.md": stolen})
        # A delete of ada plus an add of mallory is a rename only when the owner matches.
        # Here the head simply adds mallory and deletes ada.
        try:
            result = check_pr(head=head, base=base, author="mallory", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertIn("ownership", {issue.code for issue in result.issues})
        self.assertFalse(result.automerge)

    def test_binary_in_a_pull_request_is_rejected(self) -> None:
        png = (Path(__file__).resolve().parent / "fixtures" / "binary" / "avatar.png").read_bytes()
        head = _tree({"jobs/2026/11/acme-backend-engineer.md": _job(), "logo.png": "ignored"})
        (head / "logo.png").write_bytes(png)
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertIn("binary", {issue.code for issue in result.issues})
        self.assertFalse(result.automerge)

    def test_email_and_phone_in_a_post_are_rejected(self) -> None:
        dirty = _job() + "\nReach ada@gmail.com or +1 415 555 2671.\n"
        head = _tree({"jobs/2026/11/acme-backend-engineer.md": dirty})
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        found = {issue.code for issue in result.issues}
        self.assertIn("privacy-email", found)
        self.assertIn("privacy-phone", found)
        self.assertFalse(result.automerge)

    def test_shortener_is_rejected(self) -> None:
        head = _tree({"jobs/2026/11/acme-backend-engineer.md": _job(apply="https://bit.ly/acme-role")})
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertTrue(any(issue.code in {"spam-link", "schema"} for issue in result.issues))
        self.assertFalse(result.automerge)

    def test_expiry_bot_may_delete_only_expired_posts(self) -> None:
        old = _job(posted="2026-01-01")
        # Path must match the posted month.
        old_path = "jobs/2026/01/acme-backend-engineer.md"
        live = _job()
        base = _tree({old_path: old, "jobs/2026/11/acme-backend-engineer.md": live})
        head = _tree({"jobs/2026/11/acme-backend-engineer.md": live})
        try:
            ok = check_pr(head=head, base=base, author="github-actions[bot]", today=TODAY)
            bad_head = _tree({})
            bad = check_pr(head=bad_head, base=base, author="github-actions[bot]", today=TODAY)
        finally:
            shutil.rmtree(base)
            shutil.rmtree(head)
            shutil.rmtree(bad_head)
        self.assertEqual(ok.issues, [], [issue.message for issue in ok.issues])
        self.assertTrue(ok.automerge)
        self.assertIn("bot-expiry", {issue.code for issue in bad.issues})
        self.assertFalse(bad.automerge)


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
    if "posted" in extra:
        # Keep the helper honest: callers that change posted also pass a matching path.
        pass
    body = "Describe the work, the team, and the location without a phone number or an email address.\n"
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


def _talent(**extra: object) -> str:
    handle = str(extra.pop("handle", "ada"))
    meta: dict[str, object] = {
        "kind": "talent",
        "name": "Ada Lovelace",
        "github": handle,
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
    body = "A short public profile with a site link and no phone number or email address at all.\n"
    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body


def _tree(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


if __name__ == "__main__":
    unittest.main()
