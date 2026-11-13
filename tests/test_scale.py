"""Homepage, archive, and sitemap stay bounded as the board grows."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from validator.publish import (
    ARCHIVE_PAGE_SIZE,
    FEED_LIMIT,
    HOMEPAGE_PER_KIND,
    LLMS_FULL_LIMIT,
    SITEMAP_BYTE_LIMIT,
    SITEMAP_URL_LIMIT,
    write_discovery,
)

_ORIGIN = "https://softprobe.github.io/openjob"
_LOC = re.compile(r"<loc>([^<]+)</loc>")
_POST_HREF = re.compile(rf'href="({re.escape(_ORIGIN)}/p/[^"]+)"')


def _posts(count: int) -> list[dict]:
    """Newest first. Kinds rotate so each section is non-empty."""
    kinds = ("job", "talent", "talent-ref", "company")
    slugs = {"job": "jobs", "talent": "talents", "talent-ref": "talents", "company": "companies"}
    posts = []
    for index in range(count):
        kind = kinds[index % len(kinds)]
        path = f"{slugs[kind]}/x/{index:07d}.md"
        posts.append(
            {
                "kind": kind,
                "path": path,
                "title": f"Title {index}",
                "org": "Org",
                "headline": "Headline",
                "permalink": f"{_ORIGIN}/p/{path[:-3]}/",
                "posted": "2026-11-13",
                "excerpt": "A short public excerpt.",
                "location": "",
            }
        )
    return posts


def _document(posts: list[dict]) -> dict:
    return {"generated": "2026-11-13T00:00:00Z", "posts": posts}


class ScaleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.site = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.site)

    def test_small_limits_partition_posts_and_chunk_the_sitemap(self) -> None:
        posts = _posts(12)
        write_discovery(
            self.site,
            _document(posts),
            homepage_per_kind=2,
            archive_page_size=2,
            feed_limit=3,
            llms_full_limit=4,
            sitemap_url_limit=4,
            sitemap_byte_limit=50_000_000,
        )
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('href="p/'), 2 + 2 + 2)
        self.assertIn('href="jobs/page/1/"', home)
        self.assertIn('href="talents/page/1/"', home)
        self.assertIn('href="companies/page/1/"', home)
        self.assertNotIn(posts[-1]["permalink"], home)

        found = self._archive_permalinks()
        self.assertEqual(sorted(found), sorted(post["permalink"] for post in posts))
        middle = (self.site / "talents" / "page" / "2" / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="prev"', middle)
        self.assertIn('rel="next"', middle)
        self.assertIn(f'{_ORIGIN}/talents/page/1/', middle)
        self.assertIn(f'{_ORIGIN}/talents/page/3/', middle)
        last = (self.site / "talents" / "page" / "3" / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="prev"', last)
        self.assertNotIn('rel="next"', last)
        first = (self.site / "jobs" / "page" / "1" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('rel="prev"', first)
        self.assertIn('rel="next"', first)

        payload = json.loads((self.site / "feed.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["items"]), 3)
        jobs_json = json.loads((self.site / "jobs.json").read_text(encoding="utf-8"))
        self.assertEqual(len(jobs_json["items"]), 3)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("Jobs: 3.", llms)
        self.assertIn("Talent: 6.", llms)
        self.assertIn("Companies: 3.", llms)
        self.assertIn(f"{_ORIGIN}/sitemap.xml", llms)
        self.assertNotIn("/p/", llms)
        full = (self.site / "llms-full.txt").read_text(encoding="utf-8")
        self.assertEqual(full.count("Permalink:"), 4)
        self.assertIn("newest 4", full)

        locs = self._sitemap_locs()
        self.assertLessEqual(max(len(chunk) for chunk in locs), 4)
        self.assertGreater(len(locs), 1)
        flat = [loc for chunk in locs for loc in chunk]
        self.assertEqual(len(flat), len(set(flat)))
        post_locs = [loc for loc in flat if "/p/" in loc]
        self.assertEqual(sorted(post_locs), sorted(post["permalink"] for post in posts))
        self.assertIn(f"{_ORIGIN}/", flat)
        ElementTree.fromstring((self.site / "sitemap.xml").read_text(encoding="utf-8"))

    def test_byte_limit_rotates_a_sitemap_chunk(self) -> None:
        posts = _posts(30)
        limit = 700
        write_discovery(
            self.site,
            _document(posts),
            homepage_per_kind=1,
            archive_page_size=10,
            feed_limit=1,
            llms_full_limit=1,
            sitemap_url_limit=50_000,
            sitemap_byte_limit=limit,
        )
        chunks = sorted(self.site.glob("sitemap-*.xml"))
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.stat().st_size, limit)

    def test_production_limits_bound_a_large_board(self) -> None:
        count = 120_000
        posts = _posts(count)
        write_discovery(self.site, _document(posts))
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('href="p/'), HOMEPAGE_PER_KIND * 3)
        self.assertLess(len(home.encode("utf-8")), 80_000)
        self.assertIn('href="jobs/page/1/"', home)

        found = self._archive_permalinks()
        self.assertEqual(len(found), count)
        self.assertEqual(len(set(found)), count)

        self.assertEqual(len(json.loads((self.site / "feed.json").read_text(encoding="utf-8"))["items"]), FEED_LIMIT)
        self.assertEqual(len(json.loads((self.site / "jobs.json").read_text(encoding="utf-8"))["items"]), FEED_LIMIT)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertLess(len(llms.encode("utf-8")), 8_000)
        self.assertIn("Jobs: 30000.", llms)
        self.assertIn(f"{_ORIGIN}/sitemap.xml", llms)
        full = (self.site / "llms-full.txt").read_text(encoding="utf-8")
        self.assertEqual(full.count("Permalink:"), LLMS_FULL_LIMIT)
        self.assertLess(len(full.encode("utf-8")), 80_000)

        locs = self._sitemap_locs()
        per_chunk = [len(chunk) for chunk in locs]
        self.assertTrue(all(size <= SITEMAP_URL_LIMIT for size in per_chunk))
        self.assertGreater(len(locs), 1)
        self.assertEqual(sum(per_chunk), count + 1 + self._archive_page_count(posts))
        flat_posts = [loc for chunk in locs for loc in chunk if "/p/" in loc]
        self.assertEqual(len(flat_posts), count)
        self.assertEqual(len(set(flat_posts)), count)
        for chunk in self.site.glob("sitemap-*.xml"):
            self.assertLess(chunk.stat().st_size, SITEMAP_BYTE_LIMIT)

    def _archive_permalinks(self) -> list[str]:
        found: list[str] = []
        for slug in ("jobs", "talents", "companies"):
            pages = sorted((self.site / slug / "page").glob("*/index.html"), key=lambda path: int(path.parent.name))
            for page in pages:
                text = page.read_text(encoding="utf-8")
                found.extend(_POST_HREF.findall(text))
        return found

    def _sitemap_locs(self) -> list[list[str]]:
        index = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        names = [loc.rsplit("/", 1)[-1] for loc in _LOC.findall(index)]
        self.assertTrue(names)
        self.assertTrue(all(name.startswith("sitemap-") for name in names))
        return [_LOC.findall((self.site / name).read_text(encoding="utf-8")) for name in names]

    def _archive_page_count(self, posts: list[dict]) -> int:
        counts = {"job": 0, "talent": 0, "company": 0}
        for post in posts:
            kind = post["kind"]
            if kind in {"talent", "talent-ref"}:
                counts["talent"] += 1
            elif kind == "company":
                counts["company"] += 1
            else:
                counts["job"] += 1
        pages = 0
        for count in counts.values():
            pages += (count + ARCHIVE_PAGE_SIZE - 1) // ARCHIVE_PAGE_SIZE
        return pages


if __name__ == "__main__":
    unittest.main()
