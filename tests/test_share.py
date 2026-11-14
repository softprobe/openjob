"""Share text, permalinks, and the auto-merge comment."""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from samples import SAMPLES, sample_tree
from validator.index import build_index, write_pages
from validator.pr import check_pr
from validator.privacy import find_contacts, has_contact_pattern
from validator.share import (
    card_description,
    hn_title,
    pages_origin,
    permalink,
    render_body,
    share_links,
    share_text,
)

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 13)
JOB = "jobs/2026/11/acme-backend-engineer.md"
APPLY = "https://example.com/jobs/backend-engineer"
PAGE = "https://softprobe.github.io/openjob/p/jobs/2026/11/acme-backend-engineer/"
BLURB = "Backend engineer — Acme — Example City"


class ShareTextTests(unittest.TestCase):
    def test_each_kind_uses_only_the_public_fields(self) -> None:
        self.assertEqual(
            share_text(
                {
                    "kind": "job",
                    "title": "Backend engineer",
                    "company_name": "Acme",
                    "location": "Example City",
                    "apply": APPLY,
                }
            ),
            BLURB,
        )
        self.assertEqual(
            share_text(
                {
                    "kind": "talent",
                    "name": "Ada Lovelace",
                    "headline": "Engineer who ships compilers",
                    "website": "https://example.com",
                    "linkedin": "https://www.linkedin.com/in/ada",
                }
            ),
            "Engineer who ships compilers",
        )
        self.assertEqual(
            share_text(
                {
                    "kind": "company",
                    "name": "Acme",
                    "location": "Example City",
                    "website": "https://example.com",
                    "careers": "https://example.com/careers",
                }
            ),
            "Acme — Example City",
        )

    def test_urls_are_stripped_and_contacts_collapse_the_blurb(self) -> None:
        cleaned = share_text(
            {
                "kind": "job",
                "title": "Backend engineer",
                "company_name": "Acme",
                "location": "See https://example.com/apply",
            }
        )
        self.assertEqual(cleaned, "Backend engineer — Acme — See")
        self.assertNotIn("http", cleaned)
        self.assertEqual(
            share_text(
                {
                    "kind": "job",
                    "title": "Backend engineer",
                    "company_name": "Acme",
                    "location": "(415) 555-0100",
                }
            ),
            "OpenJob",
        )
        self.assertEqual(
            share_text(
                {
                    "kind": "talent",
                    "headline": "Write docs@example.com",
                }
            ),
            "OpenJob",
        )

    def test_post_allow_list_stays_and_share_text_does_not_use_it(self) -> None:
        self.assertEqual(find_contacts("Call (415) 555-0100."), [])
        self.assertEqual(find_contacts("docs@example.com"), [])
        self.assertTrue(has_contact_pattern("Call (415) 555-0100."))
        self.assertTrue(has_contact_pattern("docs@example.com"))

    def test_card_description_keeps_the_sentence_around_a_link(self) -> None:
        text = card_description("See https://example.com/apply for the role and the team today.")
        self.assertNotIn("http", text)
        self.assertIn("example.com", text)
        self.assertIn("for the role", text)
        site = card_description(
            "The public site is https://www.softprobe.ai. The company builds two products."
        )
        self.assertIn("softprobe.ai.", site)
        self.assertIn("The company builds", site)
        self.assertNotIn("The public site is The company", site)
        self.assertEqual(card_description("Write ada@gmail.com about this opening please."), "A public post on OpenJob.")

    def test_share_intents_are_public_urls(self) -> None:
        links = {item["id"]: item["href"] for item in share_links(BLURB, PAGE)}
        self.assertEqual(list(links), [
            "linkedin",
            "x",
            "reddit",
            "hackernews",
            "facebook",
            "telegram",
            "whatsapp",
            "weibo",
        ])
        self.assertEqual(parse_qs(urlparse(links["x"]).query)["text"], [BLURB])
        self.assertEqual(parse_qs(urlparse(links["x"]).query)["url"], [PAGE])
        self.assertEqual(parse_qs(urlparse(links["linkedin"]).query)["url"], [PAGE])
        self.assertNotIn("text", parse_qs(urlparse(links["linkedin"]).query))
        self.assertEqual(parse_qs(urlparse(links["facebook"]).query)["u"], [PAGE])
        self.assertEqual(parse_qs(urlparse(links["reddit"]).query)["title"], [BLURB])
        self.assertEqual(parse_qs(urlparse(links["hackernews"]).query)["t"], [BLURB])
        self.assertEqual(parse_qs(urlparse(links["telegram"]).query)["text"], [BLURB])
        whatsapp = parse_qs(urlparse(links["whatsapp"]).query)["text"][0]
        self.assertIn(BLURB, whatsapp)
        self.assertIn(PAGE, whatsapp)
        self.assertNotIn("example.com", whatsapp)
        for href in links.values():
            self.assertTrue(href.startswith("https://"))
            self.assertNotIn(APPLY, href)

    def test_hacker_news_title_stops_at_80_characters(self) -> None:
        long = "Backend engineer — " + ("Verylongcompany " * 8)
        title = hn_title(long.strip())
        self.assertLessEqual(len(title), 80)
        self.assertTrue(title.startswith("Backend engineer"))


class CommentTests(unittest.TestCase):
    def test_new_post_comment_has_links_and_no_contacts(self) -> None:
        head = _tree({JOB: _job(), "README.md": "# openjob\n"})
        base = _tree({"README.md": "# openjob\n"})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertTrue(result.automerge)
        comment = result.share_comment or ""
        self.assertTrue(comment.startswith("<!-- openjob-share -->"))
        self.assertIn(PAGE, comment)
        self.assertIn(BLURB, comment)
        for host in (
            "https://www.linkedin.com/sharing/share-offsite/",
            "https://x.com/intent/tweet?",
            "https://www.reddit.com/submit?",
            "https://news.ycombinator.com/submitlink?",
            "https://www.facebook.com/sharer/sharer.php?",
            "https://t.me/share/url?",
            "https://api.whatsapp.com/send?",
            "https://service.weibo.com/share/share.php?",
        ):
            self.assertIn(host, comment)
        quoted = [line[2:] for line in comment.splitlines() if line.startswith("> ")]
        self.assertEqual(quoted, [BLURB])
        self.assertFalse(has_contact_pattern(BLURB))
        self.assertNotIn(APPLY, comment)
        self.assertNotIn("linkedin.com/in", comment)
        self.assertNotIn("@", quoted[0])

    def test_share_links_follow_github_repository(self) -> None:
        self.assertEqual(pages_origin("softprobe/openjob"), "https://softprobe.github.io/openjob")
        self.assertEqual(pages_origin("SOFTPROBE/OpenJob"), "https://softprobe.github.io/openjob")
        self.assertEqual(pages_origin("zwobill/openjob"), "https://zwobill.github.io/openjob")
        self.assertEqual(pages_origin("softprobe/softprobe.github.io"), "https://softprobe.github.io")
        self.assertEqual(pages_origin(""), "https://softprobe.github.io/openjob")
        self.assertEqual(pages_origin("not a repo"), "https://softprobe.github.io/openjob")
        old = os.environ.get("GITHUB_REPOSITORY")
        os.environ["GITHUB_REPOSITORY"] = "zwobill/openjob"
        head = _tree({JOB: _job()})
        base = _tree({})
        try:
            comment = check_pr(head=head, base=base, author="ada", today=TODAY).share_comment or ""
        finally:
            if old is None:
                os.environ.pop("GITHUB_REPOSITORY", None)
            else:
                os.environ["GITHUB_REPOSITORY"] = old
            shutil.rmtree(head)
            shutil.rmtree(base)
        page = "https://zwobill.github.io/openjob/p/jobs/2026/11/acme-backend-engineer/"
        encoded = "https%3A%2F%2Fzwobill.github.io%2Fopenjob%2Fp%2Fjobs%2F2026%2F11%2Facme-backend-engineer%2F"
        self.assertIn(page, comment)
        self.assertIn(encoded, comment)
        self.assertNotIn("softprobe.github.io", comment)
        self.assertEqual(permalink(JOB), PAGE)

    def test_talent_comment_is_the_headline_only(self) -> None:
        rel = "talents/a/ada.md"
        head = _tree({rel: _talent()})
        base = _tree({})
        try:
            result = check_pr(head=head, base=base, author="ada", today=TODAY)
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        comment = result.share_comment or ""
        self.assertIn("Engineer who ships compilers", comment)
        self.assertNotIn("Ada Lovelace", comment)
        self.assertNotIn("example.com", comment)
        self.assertNotIn("https://github.com/ada", comment)

    def test_deletion_and_expiry_do_not_share(self) -> None:
        live = _job()
        old = _job(posted="2026-01-01")
        base = _tree({JOB: live, "jobs/2026/01/acme-backend-engineer.md": old})
        owner_base = _tree({JOB: live})
        deleted = _tree({})
        expired = _tree({JOB: live})
        try:
            owner = check_pr(head=deleted, base=owner_base, author="ada", today=TODAY)
            bot = check_pr(head=expired, base=base, author="github-actions[bot]", today=TODAY)
        finally:
            shutil.rmtree(base)
            shutil.rmtree(owner_base)
            shutil.rmtree(deleted)
            shutil.rmtree(expired)
        self.assertTrue(owner.automerge)
        self.assertIsNone(owner.share_comment)
        self.assertTrue(bot.automerge)
        self.assertIsNone(bot.share_comment)

    def test_cli_emits_the_comment_as_base64(self) -> None:
        head = _tree({JOB: _job()})
        base = _tree({})
        out = Path(tempfile.mkdtemp()) / "output.txt"
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "validator",
                    "check-pr",
                    "--head",
                    str(head),
                    "--base",
                    str(base),
                    "--author",
                    "ada",
                    "--today",
                    "2026-11-13",
                    "--github-output",
                    str(out),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            encoded = ""
            for line in out.read_text(encoding="utf-8").splitlines():
                if line.startswith("share_b64="):
                    encoded = line.split("=", 1)[1]
            comment = base64.b64decode(encoded).decode("utf-8")
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
            shutil.rmtree(out.parent)
        self.assertIn(PAGE, comment)
        self.assertNotIn(APPLY, comment)


class PageTests(unittest.TestCase):
    def test_body_urls_are_links_and_code_stays_text(self) -> None:
        page = render_body(
            "The profile pull request starts here: "
            "https://github.com/softprobe/openjob/blob/main/README.md#post-your-resume-talent.\n\n"
            "The file path is `talents/<first-letter>/<github-username>.md`.\n"
        )
        self.assertIn(
            'href="https://github.com/softprobe/openjob/blob/main/README.md#post-your-resume-talent"',
            page,
        )
        self.assertIn(
            ">https://github.com/softprobe/openjob/blob/main/README.md#post-your-resume-talent</a>.",
            page,
        )
        self.assertIn("<code>talents/&lt;first-letter&gt;/&lt;github-username&gt;.md</code>", page)
        self.assertNotIn("<first-letter>", page)
        self.assertNotIn("<github-username>", page)
        chinese = render_body("官网是 https://www.softprobe.ai。项目是 https://github.com/arextest）背后的团队。")
        self.assertIn('href="https://www.softprobe.ai"', chinese)
        self.assertIn('href="https://github.com/arextest"', chinese)
        self.assertNotIn("softprobe.ai。", chinese)
        self.assertNotIn("arextest）", chinese)

    def test_sample_pages_have_cards_and_local_scripts(self) -> None:
        root = sample_tree()
        site = Path(tempfile.mkdtemp())
        try:
            document = build_index(root, today=TODAY)
            (site / "p" / "stale").mkdir(parents=True)
            (site / "p" / "stale" / "index.html").write_text("old", encoding="utf-8")
            count = write_pages(root, site, document)
            self.assertEqual(count, len(SAMPLES))
            self.assertFalse((site / "p" / "stale").exists())
            by_path = {post["path"]: post for post in document["posts"]}
            job = by_path["jobs/2026/11/example-studio-open-source-maintainer.md"]
            talent = by_path["talents/z/zwobill.md"]
            company = by_path["companies/e/example-studio.md"]
            job_html = (site / "p" / job["path"][:-3] / "index.html").read_text(encoding="utf-8")
            talent_html = (site / "p" / talent["path"][:-3] / "index.html").read_text(encoding="utf-8")
            self.assertEqual(job["share_text"], "Example role: open source maintainer — Example Studio — Example City")
            self.assertEqual(talent["share_text"], "Format sample, not a real profile")
            self.assertNotIn("Example Candidate", talent["share_text"])
            self.assertEqual(company["share_text"], "Example Studio — Example City")
            self.assertEqual(job["permalink"], permalink(job["path"]))
            self.assertEqual(_meta(job_html, "og:title"), job["share_text"])
            self.assertEqual(_meta(job_html, "og:url"), job["permalink"])
            self.assertEqual(_name(job_html, "twitter:card"), "summary")
            self.assertEqual(_name(job_html, "twitter:title"), job["share_text"])
            head, body = job_html.split("</head>", 1)
            self.assertNotIn("example.com", head)
            self.assertNotIn("http", _meta(job_html, "og:description"))
            before, _, after = body.partition('id="share"')
            self.assertIn("https://example.com/careers/open-source-maintainer", before)
            self.assertNotIn("example.com", after)
            srcs = re.findall(r'<script[^>]+src="([^"]+)"', job_html)
            self.assertTrue(srcs)
            self.assertTrue(all(src.startswith("../") for src in srcs))
            self.assertTrue(any(src.endswith("vendor/qrcode.js") for src in srcs))
            self.assertTrue(any(src.endswith("share.js") for src in srcs))
            self.assertNotIn("cdn", job_html.lower())
            self.assertEqual(_meta(talent_html, "og:title"), talent["share_text"])
            self.assertNotIn("example.com", talent_html.split("</head>", 1)[0])
        finally:
            shutil.rmtree(site)
            shutil.rmtree(root)

    def test_marketing_is_not_in_the_repo(self) -> None:
        self.assertFalse((ROOT / "marketing").exists())
        hits: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if relative.parts and relative.parts[0] in {"jobs", "talents", "companies"}:
                continue
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if "p" in path.parts and "site" in path.parts:
                continue
            if path.name == "qrcode.js":
                continue
            if path.suffix not in {".md", ".py", ".yml", ".yaml", ".json", ".html", ".js", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "market" + "ing/" in text:
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])


def _meta(page: str, prop: str) -> str:
    match = re.search(rf'<meta property="{re.escape(prop)}" content="([^"]*)"', page)
    if match is None:
        self_fail = f"missing {prop}"
        raise AssertionError(self_fail)
    return unescape(match.group(1))


def _name(page: str, name: str) -> str:
    match = re.search(rf'<meta name="{re.escape(name)}" content="([^"]*)"', page)
    if match is None:
        raise AssertionError(f"missing {name}")
    return unescape(match.group(1))


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
        "apply": APPLY,
        "posted": "2026-11-13",
        "posted_by": "ada",
    }
    meta.update(extra)
    return _dump(meta)


def _talent() -> str:
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
    return _dump(meta)


def _dump(meta: dict[str, object]) -> str:
    body = "Describe the work, the team, and the location without a phone number or an email address.\n"
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
