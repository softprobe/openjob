"""Crawl files, structured data, and description text."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from samples import sample_tree
from validator.index import build_index, write_pages
from validator.jsonld import job_posting, places_for
from validator.prose import excerpt

TODAY = date(2026, 11, 13)
_AREX = (
    "Softprobe is hiring a software engineer. Softprobe is the team behind AREX "
    "(https://github.com/arextest), an open-source automated record/replay regression testing platform. "
    "The public site is https://www.softprobe.ai.\n\n"
    "The company builds two products. The first is automated record/replay–based Java regression testing at scale."
)


class ExcerptTests(unittest.TestCase):
    def test_parenthetical_url_does_not_eat_the_next_sentence(self) -> None:
        text = excerpt(_AREX, limit=240)
        self.assertIn("behind AREX, an open-source", text)
        self.assertNotIn("AREX ,", text)
        self.assertIn("The public site is softprobe.ai.", text)
        self.assertIn("The company builds two products.", text)
        self.assertNotIn("The public site is The company", text)
        self.assertNotIn("http", text)

    def test_markdown_link_keeps_its_label(self) -> None:
        text = excerpt("Read [AREX](https://github.com/arextest) before you apply for this role today.")
        self.assertIn("Read AREX before you apply", text)
        self.assertNotIn("http", text)

    def test_parentheses_that_are_not_urls_stay(self) -> None:
        text = excerpt("The team (Los Altos and Shanghai) is hiring a software engineer for the platform.")
        self.assertIn("(Los Altos and Shanghai)", text)

    def test_truncation_stops_on_a_word(self) -> None:
        text = excerpt("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu", limit=24)
        self.assertTrue(text.endswith("…"))
        self.assertLessEqual(len(text), 24)
        self.assertNotIn("epsil", text.rstrip("…"))
        self.assertNotRegex(text[:-1], r"\s$")


class StructuredDataTests(unittest.TestCase):
    def test_hybrid_location_is_two_places_and_not_telecommute(self) -> None:
        places = places_for("Los Altos, CA / Shanghai")
        self.assertEqual(
            places,
            [
                {"locality": "Los Altos", "region": "CA", "country": "US"},
                {"locality": "Shanghai", "country": "CN"},
            ],
        )
        posting = job_posting(
            {
                "kind": "job",
                "title": "Software Engineer",
                "path": "jobs/2026/11/softprobe-software-engineer.md",
                "permalink": "https://softprobe.github.io/openjob/p/jobs/2026/11/softprobe-software-engineer/",
                "posted": "2026-11-13",
                "expires": "2027-01-12",
                "org": "Softprobe",
                "org_website": "https://www.softprobe.ai",
                "logo": "https://example.com/logo.png",
                "location": "Los Altos, CA / Shanghai",
                "remote": "hybrid",
                "apply": "https://github.com/softprobe/openjob/blob/main/README.md",
                "apply_email": "mailto:hr@softprobe.ai",
            },
            "<p>How to apply</p>",
        )
        self.assertEqual(posting["@type"], "JobPosting")
        self.assertEqual(posting["title"], "Software Engineer")
        self.assertEqual(posting["datePosted"], "2026-11-13")
        self.assertEqual(posting["validThrough"], "2027-01-12T23:59:59Z")
        self.assertNotIn("jobLocationType", posting)
        self.assertNotIn("employmentType", posting)
        self.assertNotIn("baseSalary", posting)
        self.assertTrue(posting["directApply"])
        self.assertEqual(posting["potentialAction"]["target"], "https://github.com/softprobe/openjob/blob/main/README.md")
        self.assertEqual(
            [item["address"]["addressCountry"] for item in posting["jobLocation"]],
            ["US", "CN"],
        )
        self.assertEqual(posting["hiringOrganization"]["url"], "https://www.softprobe.ai")

    def test_fully_remote_uses_telecommute_and_not_an_office(self) -> None:
        posting = job_posting(
            {
                "title": "Engineer",
                "path": "jobs/2026/11/acme-remote.md",
                "permalink": "https://softprobe.github.io/openjob/p/jobs/2026/11/acme-remote/",
                "posted": "2026-11-13",
                "expires": None,
                "org": "Acme",
                "location": "United States",
                "remote": "remote",
                "apply": "https://jobs.example.com/role",
                "apply_email": None,
            },
            "<p>Apply on the company site.</p>",
        )
        self.assertEqual(posting["jobLocationType"], "TELECOMMUTE")
        self.assertEqual(posting["applicantLocationRequirements"]["name"], "United States")
        self.assertNotIn("jobLocation", posting)
        self.assertNotIn("validThrough", posting)
        self.assertFalse(posting["directApply"])


class BuildOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = sample_tree()
        self.site = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.root)
        shutil.rmtree(self.site)

    def test_pages_jsonld_sitemap_feeds_and_homepage_list(self) -> None:
        document = build_index(self.root, today=TODAY)
        write_pages(self.root, self.site, document)
        job = next(post for post in document["posts"] if post["kind"] == "job")
        company = next(post for post in document["posts"] if post["kind"] == "company")
        talent = next(post for post in document["posts"] if post["kind"] == "talent")
        self.assertEqual(job["company_permalink"], company["permalink"])
        self.assertTrue(company["org_website"])

        job_html = (self.site / "p" / job["path"][:-3] / "index.html").read_text(encoding="utf-8")
        company_html = (self.site / "p" / company["path"][:-3] / "index.html").read_text(encoding="utf-8")
        talent_html = (self.site / "p" / talent["path"][:-3] / "index.html").read_text(encoding="utf-8")
        home = (self.site / "index.html").read_text(encoding="utf-8")
        graph = _graph(job_html)
        types = {node["@type"] for node in graph}
        self.assertIn("JobPosting", types)
        self.assertIn("BreadcrumbList", types)
        self.assertNotIn("JobPosting", home)
        self.assertIn('"@type":"WebSite"', home)
        self.assertIn(f'href="p/{job["path"][:-3]}/"', home)
        self.assertIn("Example role: open source maintainer — Example Studio", home)
        self.assertIn("Open jobs", company_html)
        self.assertIn(job["permalink"], company_html)
        self.assertIn('"@type":"Organization"', company_html)
        self.assertIn('"@type":"Person"', talent_html)
        self.assertIn(company["permalink"], job_html)
        self.assertTrue((self.site / "p" / job["path"][:-3] / "index.md").is_file())
        head, _body = job_html.split("</head>", 1)
        self.assertIn('rel="canonical"', head)
        self.assertIn("og:description", head)
        self.assertNotIn("http://", _meta_content(head, "og:description"))

        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://softprobe.github.io/openjob/</loc>", sitemap)
        self.assertIn(job["permalink"], sitemap)
        self.assertIn(company["permalink"], sitemap)
        self.assertIn(talent["permalink"], sitemap)
        self.assertNotIn("?kind=", sitemap)
        ElementTree.fromstring(sitemap)

        robots = (self.site / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://softprobe.github.io/openjob/sitemap.xml", robots)

        feed = (self.site / "feed.xml").read_text(encoding="utf-8")
        jobs_feed = (self.site / "jobs.xml").read_text(encoding="utf-8")
        ElementTree.fromstring(feed)
        ElementTree.fromstring(jobs_feed)
        self.assertIn("Example role: open source maintainer", feed)
        self.assertIn(talent["title"], feed)
        self.assertIn("Example role: open source maintainer", jobs_feed)
        self.assertNotIn(talent["title"], jobs_feed)
        ElementTree.fromstring((self.site / "atom.xml").read_text(encoding="utf-8"))
        jobs_atom = ElementTree.fromstring((self.site / "jobs.atom").read_text(encoding="utf-8"))
        atom_titles = [node.text for node in jobs_atom.findall("{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title")]
        self.assertTrue(any("Example role" in (title or "") for title in atom_titles))
        self.assertFalse(any(talent["title"] in (title or "") for title in atom_titles))

        payload = json.loads((self.site / "feed.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "https://jsonfeed.org/version/1.1")
        self.assertEqual(len(payload["items"]), 3)
        jobs_json = json.loads((self.site / "jobs.json").read_text(encoding="utf-8"))
        self.assertEqual(len(jobs_json["items"]), 1)

        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(llms.startswith("# OpenJob\n"))
        self.assertIn(job["permalink"], llms)
        full = (self.site / "llms-full.txt").read_text(encoding="utf-8")
        self.assertIn("## FAQ", full)
        self.assertIn(job["permalink"], full)
        self.assertTrue((self.site / "404.html").is_file() or (Path(__file__).parents[1] / "site" / "404.html").is_file())


def _graph(page: str) -> list[dict]:
    start = page.index('type="application/ld+json">') + len('type="application/ld+json">')
    end = page.index("</script>", start)
    data = json.loads(page[start:end])
    graph = data.get("@graph")
    self_type = data.get("@type")
    if isinstance(graph, list):
        return graph
    return [data] if self_type else []


def _meta_content(head: str, prop: str) -> str:
    needle = f'property="{prop}" content="'
    start = head.index(needle) + len(needle)
    end = head.index('"', start)
    return head[start:end]


if __name__ == "__main__":
    unittest.main()
