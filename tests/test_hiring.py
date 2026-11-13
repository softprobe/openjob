"""Hiring addresses on jobs, and company logo URLs."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from validator.index import build_index, write_pages
from validator.posts import validate_post
from validator.pr import check_pr
from validator.privacy import find_contacts, has_contact_pattern

TODAY = date(2026, 11, 13)
JOB = "jobs/2026/11/softprobe-software-engineer.md"
COMPANY = "companies/s/softprobe.md"
TALENT = "talents/a/ada.md"
BODY = "Build the record and replay engine and the agent observability product with the team.\n"
HIRING = "mailto:hr@softprobe.ai"
LOGO = "https://cdn.example.com/softprobe.svg"


def codes(issues: list) -> set[str]:
    return {issue.code for issue in issues}


class HiringEmailTests(unittest.TestCase):
    def test_matching_domain_in_apply_is_allowed(self) -> None:
        root = _tree(
            {
                COMPANY: _company(),
                JOB: _job(apply=HIRING),
            }
        )
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [f"{issue.code}: {issue.message}" for issue in issues])

    def test_matching_domain_in_apply_email_keeps_the_https_link(self) -> None:
        root = _tree(
            {
                COMPANY: _company(),
                JOB: _job(apply_email=HIRING),
            }
        )
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
            document = build_index(root, today=TODAY)
            site = Path(tempfile.mkdtemp())
            write_pages(root, site, document)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [f"{issue.code}: {issue.message}" for issue in issues])
        post = next(item for item in document["posts"] if item["path"] == JOB)
        self.assertEqual(post["apply"], "https://www.softprobe.ai/jobs")
        self.assertEqual(post["apply_email"], HIRING)
        self.assertEqual(post["share_text"], "Software engineer — Softprobe — Los Altos")
        self.assertNotIn("hr@softprobe.ai", post["share_text"])
        self.assertFalse(has_contact_pattern(post["share_text"]))
        for share in post["shares"]:
            self.assertNotIn("mailto:", share["href"])
            self.assertNotIn("hr@", share["href"])
        page = (site / "p" / JOB[:-3] / "index.html").read_text(encoding="utf-8")
        shutil.rmtree(site)
        head, body = page.split("</head>", 1)
        self.assertNotIn("hr@softprobe.ai", head)
        self.assertNotIn("mailto:", head)
        before, _, after = body.partition('id="share"')
        self.assertIn("Apply by email", before)
        self.assertIn(HIRING, before)
        self.assertIn("https://www.softprobe.ai/jobs", before)
        self.assertNotIn("hr@softprobe.ai", after)
        self.assertNotIn("mailto:", after)

    def test_job_website_is_used_when_there_is_no_company_page(self) -> None:
        root = _tree({JOB: _job(apply=HIRING, website="https://www.softprobe.ai")})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [f"{issue.code}: {issue.message}" for issue in issues])

    def test_quoted_apply_email_matches_www_website(self) -> None:
        text = _job(apply="https://www.linkedin.com/company/softprobe/jobs/")
        text = text.replace(
            "posted_by: ada\n",
            'posted_by: ada\napply_email: "mailto:hr@softprobe.ai"\n',
        )
        root = _tree({COMPANY: _company(), JOB: text})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [f"{issue.code}: {issue.message}" for issue in issues])

    def test_mismatched_domain_is_rejected(self) -> None:
        root = _tree({COMPANY: _company(), JOB: _job(apply="mailto:hr@gmail.com")})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("gmail.com" in issue.message and "softprobe.ai" in issue.message for issue in issues))
        self.assertNotIn("phone", codes(issues))

    def test_company_page_wins_over_a_job_website(self) -> None:
        root = _tree(
            {
                COMPANY: _company(),
                JOB: _job(apply="mailto:hr@gmail.com", website="https://gmail.com"),
            }
        )
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("gmail.com" in issue.message and "softprobe.ai" in issue.message for issue in issues))

    def test_email_domain_must_match_whole_labels(self) -> None:
        root = _tree({COMPANY: _company(), JOB: _job(apply="mailto:hr@probe.ai")})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("`probe.ai`" in issue.message for issue in issues))

    def test_email_in_a_talent_post_is_rejected(self) -> None:
        body = "Engineer who ships compilers and can be reached at hr@softprobe.ai for contract work.\n"
        root = _tree({TALENT: _talent(body=body)})
        try:
            issues = validate_post(root=root, rel=TALENT, today=TODAY, author="ada", new_file=True)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("looks like an email" in issue.message for issue in issues))

    def test_email_in_the_job_body_is_rejected(self) -> None:
        body = "Write to hr@softprobe.ai if the form is down. The team is in Los Altos.\n"
        root = _tree({COMPANY: _company(), JOB: _job(body=body)})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY, author="ada", new_file=True)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("looks like an email" in issue.message for issue in issues))

    def test_body_copy_is_rejected_even_when_apply_email_matches(self) -> None:
        body = "The hiring address is hr@softprobe.ai and the team is in Los Altos.\n"
        root = _tree({COMPANY: _company(), JOB: _job(apply=HIRING, body=body)})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-email", codes(issues))
        self.assertTrue(any("looks like an email" in issue.message for issue in issues))

    def test_phone_numbers_still_fail(self) -> None:
        body = BODY + "Call +1 415 555 2671 about the role.\n"
        root = _tree({COMPANY: _company(), JOB: _job(apply=HIRING, body=body)})
        try:
            issues = validate_post(root=root, rel=JOB, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertIn("privacy-phone", codes(issues))
        self.assertNotIn("privacy-email", codes(issues))

    def test_scanner_still_flags_the_address_outside_a_job_field(self) -> None:
        self.assertIn("email", {item.kind for item in find_contacts(HIRING)})

    def test_one_valid_post_can_still_automerge(self) -> None:
        base = _tree({COMPANY: _company()})
        head = _tree({COMPANY: _company(), JOB: _job(apply_email=HIRING)})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(base)
            shutil.rmtree(head)
        self.assertEqual(result.issues, [], [issue.message for issue in result.issues])
        self.assertTrue(result.automerge)
        comment = result.share_comment or ""
        self.assertNotIn("hr@softprobe.ai", comment)
        self.assertNotIn("mailto:", comment)
        self.assertIn("Software engineer — Softprobe — Los Altos", comment)


class LogoTests(unittest.TestCase):
    def test_https_logo_is_indexed_and_rendered(self) -> None:
        root = _tree({COMPANY: _company(logo=LOGO)})
        site = Path(tempfile.mkdtemp())
        try:
            issues = validate_post(root=root, rel=COMPANY, today=TODAY, author="ada", new_file=True)
            document = build_index(root, today=TODAY)
            write_pages(root, site, document)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [issue.message for issue in issues])
        post = document["posts"][0]
        self.assertEqual(post["logo"], LOGO)
        self.assertNotIn("cdn.example.com", post["share_text"])
        self.assertEqual(post["share_text"], "Softprobe — Los Altos")
        page = (site / "p" / "companies" / "s" / "softprobe" / "index.html").read_text(encoding="utf-8")
        shutil.rmtree(site)
        self.assertIn(f'<img class="logo" src="{LOGO}"', page)
        self.assertIn('width="48"', page)
        self.assertIn('height="48"', page)
        self.assertIn('referrerpolicy="no-referrer"', page)
        head, _body = page.split("</head>", 1)
        self.assertNotIn(LOGO, head)

    def test_job_copies_the_company_logo(self) -> None:
        root = _tree({COMPANY: _company(logo=LOGO), JOB: _job()})
        site = Path(tempfile.mkdtemp())
        try:
            document = build_index(root, today=TODAY)
            write_pages(root, site, document)
        finally:
            shutil.rmtree(root)
        by_path = {post["path"]: post for post in document["posts"]}
        self.assertEqual(by_path[COMPANY]["logo"], LOGO)
        self.assertEqual(by_path[JOB]["logo"], LOGO)
        self.assertNotIn(LOGO, by_path[JOB]["share_text"])
        self.assertNotIn("cdn.example.com", by_path[JOB]["share_text"])
        page = (site / "p" / JOB[:-3] / "index.html").read_text(encoding="utf-8")
        shutil.rmtree(site)
        self.assertIn(f'<img class="logo" src="{LOGO}" alt="Softprobe" width="48" height="48"', page)
        self.assertIn('class="identity"', page)
        head, _body = page.split("</head>", 1)
        self.assertNotIn(LOGO, head)

    def test_job_without_a_company_logo_stays_blank(self) -> None:
        root = _tree({COMPANY: _company(), JOB: _job()})
        try:
            document = build_index(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        job = next(post for post in document["posts"] if post["path"] == JOB)
        company = next(post for post in document["posts"] if post["path"] == COMPANY)
        self.assertIsNone(job["logo"])
        self.assertIsNone(company["logo"])

    def test_job_without_a_company_page_has_no_logo(self) -> None:
        root = _tree({JOB: _job()})
        try:
            document = build_index(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertIsNone(document["posts"][0]["logo"])

    def test_logo_must_be_https(self) -> None:
        for logo in ("logo.png", "http://cdn.example.com/logo.png", "https://cdn.example.com/logo.png "):
            with self.subTest(logo=logo):
                root = _tree({COMPANY: _company(logo=logo)})
                try:
                    issues = validate_post(root=root, rel=COMPANY, today=TODAY)
                finally:
                    shutil.rmtree(root)
                self.assertIn("schema", codes(issues))


def _company(**extra: object) -> str:
    meta: dict[str, object] = {
        "kind": "company",
        "slug": "softprobe",
        "name": "Softprobe",
        "website": "https://www.softprobe.ai",
        "location": "Los Altos",
        "tags": ["observability"],
        "posted": "2026-11-13",
        "posted_by": "ada",
    }
    meta.update(extra)
    return _dump(
        meta,
        "Softprobe builds record and replay testing and agent observability for engineering teams.\n",
    )


def _job(**extra: object) -> str:
    body = str(extra.pop("body", BODY))
    meta: dict[str, object] = {
        "kind": "job",
        "title": "Software engineer",
        "company": "softprobe",
        "company_name": "Softprobe",
        "role_slug": "software-engineer",
        "location": "Los Altos",
        "remote": "hybrid",
        "languages": ["en"],
        "tags": ["java"],
        "apply": "https://www.softprobe.ai/jobs",
        "posted": "2026-11-13",
        "posted_by": "ada",
    }
    meta.update(extra)
    return _dump(meta, body)


def _talent(**extra: object) -> str:
    body = str(extra.pop("body", "A short public profile with a site link and no phone number or email address.\n"))
    meta: dict[str, object] = {
        "kind": "talent",
        "name": "Ada Lovelace",
        "github": "ada",
        "headline": "Engineer who ships compilers",
        "location": "Los Altos",
        "remote": True,
        "languages": ["en"],
        "tags": ["compilers"],
        "open_to": ["contract"],
        "website": "https://example.com",
        "posted": "2026-11-13",
    }
    meta.update(extra)
    return _dump(meta, body)


def _dump(meta: dict[str, object], body: str) -> str:
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
