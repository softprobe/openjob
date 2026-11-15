"""Seekers and employers get equal paths: prompts, apply labels, talent contact, feeds, 404."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from validator.publish import write_discovery
from validator.share import is_profile_guide, profile_guide_url, render_post_page

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://softprobe.github.io/openjob"
GUIDE = "https://github.com/softprobe/openjob/blob/main/README.md#post-your-resume-talent"


class ProfileGuideTests(unittest.TestCase):
    def test_a_profile_guide_is_not_labeled_apply(self) -> None:
        self.assertTrue(is_profile_guide(GUIDE))
        self.assertTrue(is_profile_guide("https://github.com/softprobe/openjob#add-your-profile"))
        self.assertTrue(is_profile_guide(f"{ORIGIN}/p/jobs/2026/11/example/"))
        self.assertFalse(is_profile_guide("https://example.com/jobs/backend-engineer"))
        self.assertFalse(is_profile_guide("mailto:jobs@example.com"))
        page = render_post_page(
            _job(apply=GUIDE, apply_email="mailto:jobs@example.com"),
            "The role is described here for the hiring team.\n",
        )
        self.assertNotIn('data-i18n="apply"', page)
        self.assertNotIn("post-your-resume-talent", page)
        self.assertNotIn('"@type":"ApplyAction","target":"' + GUIDE, page)
        self.assertIn('"target":"mailto:jobs@example.com"', page)
        self.assertIn('data-i18n="applyEmail"', page)
        self.assertIn('data-i18n="alsoProfile"', page)
        self.assertIn(profile_guide_url(), page)
        real = render_post_page(
            _job(apply="https://example.com/jobs/backend-engineer"),
            "The role is described here for the hiring team.\n",
        )
        self.assertIn('data-i18n="apply">Apply', real)
        self.assertNotIn('data-i18n="alsoProfile"', real)

    def test_configured_origin_is_not_an_apply_link(self) -> None:
        previous = os.environ.get("PAGES_ORIGIN")
        os.environ["PAGES_ORIGIN"] = "https://openjob.softprobe.ai"
        try:
            self.assertTrue(is_profile_guide("https://openjob.softprobe.ai/about/"))
            self.assertFalse(is_profile_guide("https://www.softprobe.ai/"))
        finally:
            if previous is None:
                os.environ.pop("PAGES_ORIGIN", None)
            else:
                os.environ["PAGES_ORIGIN"] = previous


class TalentContactTests(unittest.TestCase):
    def test_permalink_labels_github_linkedin_website_and_open_to(self) -> None:
        page = render_post_page(
            _talent(),
            "Ada writes about the work she wants. There is no phone number here.\n",
        )
        self.assertIn('data-i18n="github">GitHub', page)
        self.assertIn('href="https://github.com/ada"', page)
        self.assertIn('data-i18n="linkedin">LinkedIn', page)
        self.assertIn("https://www.linkedin.com/in/ada", page)
        self.assertIn('data-i18n="website">Website', page)
        self.assertIn("https://example.com", page)
        self.assertIn('data-i18n="openTo.contract">Contract', page)
        self.assertIn('data-i18n="reachNote"', page)
        self.assertIn("does not list an email or a phone number", page)
        self.assertNotIn("mailto:", page)
        self.assertNotIn('data-i18n="profile"', page)


class DiscoverySideTests(unittest.TestCase):
    def test_find_work_and_empty_talent_feed(self) -> None:
        site = Path(tempfile.mkdtemp())
        try:
            write_discovery(site, {"generated": "2026-11-14T00:00:00Z", "posts": []})
            llms = (site / "llms.txt").read_text(encoding="utf-8")
            full = (site / "llms-full.txt").read_text(encoding="utf-8")
            talents = (site / "talents.xml").read_text(encoding="utf-8")
            archive = (site / "talents" / "page" / "1" / "index.html").read_text(encoding="utf-8")
            missing = (site / "404.html").read_text(encoding="utf-8")
            catalog = json.loads((site / "schema" / "index.json").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(site)
        self.assertIn("## Find work", llms)
        self.assertLess(llms.index("## Find work"), llms.index("## Post"))
        self.assertIn("https://openjob.softprobe.ai/index.json", llms)
        self.assertNotIn("softprobe.github.io/openjob/index.json", llms)
        self.assertIn(f"{ORIGIN}/jobs.json", llms)
        self.assertIn(f"{ORIGIN}/talents.xml", llms)
        self.assertIn(f"{ORIGIN}/schema/talent.json", llms)
        self.assertIn("resume", llms.lower())
        self.assertIn("not an application", llms)
        self.assertIn("How do I add a profile?", full)
        self.assertIn("/talents.xml", full)
        self.assertIn("A link to this board's profile guide is not an application.", full)
        ElementTree.fromstring(talents)
        self.assertIn("OpenJob talent", talents)
        self.assertIn('data-i18n="emptyLead.talent"', archive)
        self.assertEqual(catalog["title"], "OpenJob public index")
        self.assertEqual(catalog["$id"], f"{ORIGIN}/schema/index.json")
        self.assertIn('href="/style.css"', missing)
        self.assertIn('src="/i18n.js"', missing)
        self.assertNotIn('href="style.css"', missing)
        self.assertNotIn('src="i18n.js"', missing)

    def test_404_back_link_uses_the_configured_origin(self) -> None:
        previous = os.environ.get("PAGES_ORIGIN")
        os.environ["PAGES_ORIGIN"] = "https://openjob.softprobe.ai"
        site = Path(tempfile.mkdtemp())
        try:
            write_discovery(site, {"generated": "2026-11-14T00:00:00Z", "posts": []})
            missing = (site / "404.html").read_text(encoding="utf-8")
        finally:
            shutil.rmtree(site)
            if previous is None:
                os.environ.pop("PAGES_ORIGIN", None)
            else:
                os.environ["PAGES_ORIGIN"] = previous
        self.assertIn('href="https://openjob.softprobe.ai/"', missing)
        self.assertNotIn("github.io", missing)
        self.assertIn('href="/style.css"', missing)


class InterfaceCopyTests(unittest.TestCase):
    def test_homepage_offers_both_audiences_and_seeker_prompts(self) -> None:
        home = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        strings = (ROOT / "site" / "i18n.js").read_text(encoding="utf-8")
        about = (ROOT / "site" / "about" / "index.html").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("The open job index for AI agents", home)
        self.assertIn("https://openjob.softprobe.ai/index.json", home)
        self.assertNotIn("softprobe.github.io/openjob/index.json", home)
        self.assertIn("Find me a job", home)
        self.assertIn("Post our role", home)
        self.assertIn("Add my profile", home)
        self.assertIn("Do it by hand", home)
        self.assertIn('data-prompt="find"', home)
        self.assertIn('data-prompt="job"', home)
        self.assertIn('data-prompt="talent"', home)
        self.assertIn("search_jobs", home)
        self.assertIn('href="jobs.xml"', home)
        self.assertIn('href="talents.xml"', home)
        self.assertIn("agentForFilter", script)
        self.assertIn('audienceChoice === "looking"', script)
        self.assertIn('return "talent"', script)
        self.assertIn('audienceChoice === "hiring"', script)
        self.assertIn('return "job"', script)
        self.assertIn("isProfileGuide", script)
        self.assertIn('state.kind === "talent"', script)
        self.assertIn("面向 AI 代理的开放职位索引", strings)
        self.assertIn("https://openjob.softprobe.ai/index.json", strings)
        self.assertIn("帮我找工作", strings)
        self.assertIn("发布我们的职位", strings)
        self.assertIn("添加我的档案", strings)
        self.assertIn("自己动手", strings)
        self.assertIn("也可以添加档案", strings)
        self.assertIn("看板上不列出邮箱或电话", strings)
        self.assertIn("新职位", strings)
        self.assertIn("新档案", strings)
        self.assertIn('data-i18n="aboutFeeds"', about)
        self.assertIn("../jobs.xml", about)
        self.assertIn("../talents.xml", about)
        self.assertIn("## Search the board", agents)
        self.assertIn("index.json", agents)
        self.assertIn("not an application", agents)
        self.assertIn("search_jobs", agents)
        self.assertIn("create_or_update_post", agents)
        self.assertIn("Who can edit what", agents)


def _job(**extra: object) -> dict:
    post = {
        "kind": "job",
        "title": "Backend engineer",
        "path": "jobs/2026/11/acme-backend-engineer.md",
        "permalink": f"{ORIGIN}/p/jobs/2026/11/acme-backend-engineer/",
        "share_text": "Backend engineer — Acme — Example City",
        "excerpt": "A short public excerpt for the role.",
        "org": "Acme",
        "location": "Example City",
        "remote": "remote",
        "languages": ["en"],
        "tags": ["backend"],
        "posted": "2026-11-14",
        "shares": [],
    }
    post.update(extra)
    return post


def _talent() -> dict:
    return {
        "kind": "talent",
        "title": "Ada Lovelace",
        "path": "talents/ada.md",
        "permalink": f"{ORIGIN}/p/talents/ada/",
        "share_text": "Site reliability engineer open to contract work",
        "excerpt": "A short public excerpt for the profile.",
        "headline": "Site reliability engineer open to contract work",
        "owner": "ada",
        "location": "London",
        "remote": "remote",
        "languages": ["en"],
        "tags": ["reliability"],
        "open_to": ["contract"],
        "website": "https://example.com",
        "linkedin": "https://www.linkedin.com/in/ada",
        "posted": "2026-11-14",
        "shares": [],
    }


if __name__ == "__main__":
    unittest.main()
