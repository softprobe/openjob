"""Site chrome is English in the static HTML and switches in the browser."""

from __future__ import annotations

import unittest
from pathlib import Path

from validator.publish import _llms_full
from validator.share import render_post_page

ROOT = Path(__file__).resolve().parents[1]
BODY = "这是作者写的正文，界面语言不应该改掉这句话。\n"


def _post(**extra: object) -> dict:
    post = {
        "kind": "job",
        "title": "Example role",
        "path": "jobs/2026/11/example-role.md",
        "permalink": "https://softprobe.github.io/openjob/p/jobs/2026/11/example-role/",
        "share_text": "Example role — Example Studio — Example City",
        "excerpt": "A short English excerpt.",
        "org": "Example Studio",
        "location": "Example City",
        "remote": "hybrid",
        "languages": ["en", "zh"],
        "tags": ["docs"],
        "apply": "https://example.com/apply",
        "apply_email": "mailto:jobs@example.com",
        "posted": "2026-11-13",
        "expires": "2027-01-12",
        "employment_type": "FULL_TIME",
        "shares": [],
    }
    post.update(extra)
    return post


class InterfaceLanguageTests(unittest.TestCase):
    def test_static_job_page_is_english_and_keeps_the_post(self) -> None:
        page = render_post_page(_post(), BODY)
        self.assertIn('<html lang="en">', page)
        self.assertIn('data-i18n="howToApply">How to apply', page)
        self.assertIn('data-i18n="copyEmail"', page)
        self.assertIn(">Copy email<", page)
        self.assertIn('data-i18n="kind.job">Job', page)
        self.assertIn('data-i18n="remoteOpt.hybrid">Hybrid', page)
        self.assertIn('data-i18n="employment.FULL_TIME">Full-time', page)
        self.assertIn('src="../../../../../i18n.js"', page)
        self.assertNotIn("如何申请", page)
        self.assertNotIn("Job · 职位", page)
        self.assertNotIn("Board · 公告板", page)
        self.assertIn(BODY.strip(), page)
        self.assertIn("Example role — Example Studio — Example City", page)

    def test_chinese_only_post_keeps_a_chinese_page_language(self) -> None:
        page = render_post_page(_post(languages=["zh"]), BODY)
        self.assertIn('<html lang="zh">', page)
        self.assertIn('data-i18n="howToApply">How to apply', page)
        self.assertNotIn("如何申请", page)
        self.assertIn(BODY.strip(), page)

    def test_browser_script_chooses_from_languages_then_saves_the_choice(self) -> None:
        script = (ROOT / "site" / "i18n.js").read_text(encoding="utf-8")
        self.assertIn("navigator.languages", script)
        self.assertIn("openjob-ui", script)
        self.assertIn("localStorage", script)
        self.assertNotIn("如何申请", (ROOT / "site" / "index.html").read_text(encoding="utf-8"))
        about = (ROOT / "site" / "about" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<h2>中文</h2>", about)
        self.assertIn('data-i18n="aboutLanguages"', about)
        self.assertIn("exactly <code>zh</code>", about)

    def test_llms_faq_stays_english(self) -> None:
        text = _llms_full([], 1)
        self.assertIn(
            "The page language is Chinese only when languages is exactly zh.",
            text,
        )
        self.assertNotIn("如何申请", text)


if __name__ == "__main__":
    unittest.main()
