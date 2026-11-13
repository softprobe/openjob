"""Sitemap, robots, feeds, llms.txt, and the no-JS homepage list.

``robots.txt`` is written next to the other site files. On a github.io project
site, crawlers request robots.txt from the host root, which this file is not.
It becomes the host file when the board is served from its own domain.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from validator.share import PAGES_ORIGIN

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "site" / "index.html"
_ORIGIN = PAGES_ORIGIN.rstrip("/")
_HOME = _ORIGIN + "/"
_POSITIONING = (
    "OpenJob is a job board that lives in a Git repository: you post a role or a profile "
    "with a pull request, people find it on a static page, and the file expires unless someone renews it."
)


def write_discovery(site_dir: Path, document: dict) -> None:
    posts = list(document["posts"])
    generated = str(document.get("generated") or "")
    lastmod = generated[:10] if len(generated) >= 10 else datetime.now(timezone.utc).date().isoformat()
    (site_dir / "sitemap.xml").write_text(_sitemap(posts, lastmod), encoding="utf-8")
    (site_dir / "robots.txt").write_text(_robots(), encoding="utf-8")
    (site_dir / "feed.xml").write_text(_rss(posts, "OpenJob", f"{_ORIGIN}/feed.xml"), encoding="utf-8")
    jobs = [post for post in posts if post.get("kind") == "job"]
    (site_dir / "jobs.xml").write_text(_rss(jobs, "OpenJob jobs", f"{_ORIGIN}/jobs.xml"), encoding="utf-8")
    (site_dir / "atom.xml").write_text(_atom(posts, "OpenJob", f"{_ORIGIN}/atom.xml"), encoding="utf-8")
    (site_dir / "jobs.atom").write_text(_atom(jobs, "OpenJob jobs", f"{_ORIGIN}/jobs.atom"), encoding="utf-8")
    (site_dir / "feed.json").write_text(_json_feed(posts, "OpenJob", f"{_ORIGIN}/feed.json"), encoding="utf-8")
    (site_dir / "jobs.json").write_text(_json_feed(jobs, "OpenJob jobs", f"{_ORIGIN}/jobs.json"), encoding="utf-8")
    (site_dir / "llms.txt").write_text(_llms(posts), encoding="utf-8")
    (site_dir / "llms-full.txt").write_text(_llms_full(posts), encoding="utf-8")
    _write_homepage(site_dir, posts)


def _write_homepage(site_dir: Path, posts: list[dict]) -> None:
    template = _TEMPLATE.read_text(encoding="utf-8")
    marker = "<!-- openjob:posts -->"
    if marker not in template:
        raise ValueError("site/index.html is missing the <!-- openjob:posts --> marker")
    page = template.replace(marker, _post_list(posts), 1)
    (site_dir / "index.html").write_text(page, encoding="utf-8")


def _post_list(posts: list[dict]) -> str:
    items = []
    for post in posts:
        href = "p/" + str(post["path"]).removesuffix(".md") + "/"
        items.append(f'<li><a href="{escape(href)}">{escape(_label(post))}</a></li>')
    if not items:
        return '<p id="post-list">No posts yet.</p>'
    return '<ul id="post-list">\n' + "\n".join(items) + "\n</ul>"


def _label(post: dict) -> str:
    kind = post.get("kind")
    title = str(post.get("title") or "")
    if kind == "job":
        org = str(post.get("org") or "")
        return f"{title} — {org}" if org else title
    if kind in {"talent", "talent-ref"}:
        headline = str(post.get("headline") or "")
        return f"{title} — {headline}" if headline else title
    return title


def _sitemap(posts: list[dict], lastmod: str) -> str:
    urls = [
        "  <url>",
        f"    <loc>{escape(_HOME)}</loc>",
        f"    <lastmod>{escape(lastmod)}</lastmod>",
        "  </url>",
    ]
    for post in posts:
        posted = str(post.get("posted") or lastmod)
        urls.extend(
            [
                "  <url>",
                f"    <loc>{escape(str(post['permalink']))}</loc>",
                f"    <lastmod>{escape(posted)}</lastmod>",
                "  </url>",
            ]
        )
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )


def _robots() -> str:
    return (
        "# On a github.io project site, crawlers read the host root robots.txt,\n"
        "# not this file. This file applies once the board has its own hostname.\n"
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {_ORIGIN}/sitemap.xml\n"
    )


def _rss(posts: list[dict], title: str, self_url: str) -> str:
    items = []
    for post in posts:
        posted = _rfc822(str(post.get("posted") or ""))
        link = escape(str(post["permalink"]))
        items.append(
            "\n".join(
                [
                    "    <item>",
                    f"      <title>{escape(_label(post))}</title>",
                    f"      <link>{link}</link>",
                    f"      <guid isPermaLink=\"true\">{link}</guid>",
                    f"      <pubDate>{escape(posted)}</pubDate>",
                    f"      <description>{escape(str(post.get('excerpt') or ''))}</description>",
                    f"      <category>{escape(str(post.get('kind') or ''))}</category>",
                    "    </item>",
                ]
            )
        )
    inner = "\n".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{escape(title)}</title>\n"
        f"    <link>{escape(_HOME)}</link>\n"
        f"    <description>{escape(_POSITIONING)}</description>\n"
        f"    <atom:link xmlns:atom=\"http://www.w3.org/2005/Atom\" href=\"{escape(self_url)}\" rel=\"self\" type=\"application/rss+xml\"/>\n"
        f"{inner}\n"
        "  </channel>\n"
        "</rss>\n"
    )


def _atom(posts: list[dict], title: str, self_url: str) -> str:
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for post in posts:
        posted = str(post.get("posted") or "1970-01-01") + "T00:00:00Z"
        link = escape(str(post["permalink"]))
        entries.append(
            "\n".join(
                [
                    "  <entry>",
                    f"    <title>{escape(_label(post))}</title>",
                    f"    <link href=\"{link}\" rel=\"alternate\"/>",
                    f"    <id>{link}</id>",
                    f"    <updated>{escape(posted)}</updated>",
                    f"    <summary>{escape(str(post.get('excerpt') or ''))}</summary>",
                    f"    <category term=\"{escape(str(post.get('kind') or ''))}\"/>",
                    "  </entry>",
                ]
            )
        )
    inner = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f"  <title>{escape(title)}</title>\n"
        f"  <link href=\"{escape(_HOME)}\" rel=\"alternate\"/>\n"
        f"  <link href=\"{escape(self_url)}\" rel=\"self\"/>\n"
        f"  <id>{escape(_HOME)}</id>\n"
        f"  <updated>{updated}</updated>\n"
        f"{inner}\n"
        "</feed>\n"
    )


def _json_feed(posts: list[dict], title: str, self_url: str) -> str:
    items = []
    for post in posts:
        posted = str(post.get("posted") or "1970-01-01") + "T00:00:00Z"
        items.append(
            {
                "id": post["permalink"],
                "url": post["permalink"],
                "title": _label(post),
                "content_text": post.get("excerpt") or "",
                "date_published": posted,
                "tags": [post.get("kind") or ""],
            }
        )
    document = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": title,
        "home_page_url": _HOME,
        "feed_url": self_url,
        "description": _POSITIONING,
        "items": items,
    }
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def _llms(posts: list[dict]) -> str:
    lines = [
        "# OpenJob",
        "",
        f"> {_POSITIONING}",
        "",
        "Jobs, talent profiles, and company pages are Markdown files in a public GitHub repository. "
        "There are no accounts and no tracking. Phone numbers are not allowed. A job may show one "
        "hiring address when its domain matches the company website. Jobs last 60 days and talent "
        "profiles last 180 days unless renewed. Company pages do not expire. Expired posts leave "
        f"the index at {_ORIGIN}/index.json.",
        "",
        "## Posts",
        "",
    ]
    for post in posts:
        note = str(post.get("excerpt") or "").replace("\n", " ")
        lines.append(f"- [{_label(post)}]({post['permalink']}): {note}")
        source = post.get("source_url")
        if source:
            lines.append(f"  - [Markdown source]({source})")
    lines.extend(
        [
            "",
            "## Docs",
            "",
            "- [README](https://github.com/softprobe/openjob/blob/main/README.md)",
            "- [Contributing](https://github.com/softprobe/openjob/blob/main/CONTRIBUTING.md)",
            f"- [Live index]({_ORIGIN}/index.json)",
            f"- [About]({_ORIGIN}/about/)",
            "",
        ]
    )
    return "\n".join(lines)


def _llms_full(posts: list[dict]) -> str:
    faq = """## FAQ

What is OpenJob?
OpenJob is a job board stored as Markdown in a Git repository. A pull request publishes a job, a talent profile, or a company page. Readers open a static page. The file expires unless someone renews it.

How do I post a job or a talent profile?
Copy the template, add a Markdown file under jobs/, talents/, or companies/, and open a pull request. The checker validates it. A post-only pull request merges on its own.

How do I apply?
The job page shows the application method: an email on the company domain, an https link, or both. A talent profile is another pull request under talents/. Do not put a phone number or a personal email in the profile.

Why are phone numbers and personal emails rejected?
The board is public. Phone numbers are never accepted. Talent posts cannot contain an email. A job may list one hiring address, and only when that domain matches the company website.

How long does a post stay up, and how do I renew it?
A job lasts 60 days and a talent profile lasts 180 days, counted from posted or renewed. Set renewed in a pull request to keep it. Company pages stay until the owner deletes them. An expired post is removed and its page is gone.

Can a post be in English and Chinese?
Yes. One file can contain both. The page language is Chinese only when languages is exactly zh. There are no separate language URLs.

Who maintains this, and can I fork it?
Softprobe maintains https://github.com/softprobe/openjob. Posts are CC BY 4.0. Code is MIT. You can fork the repository.
"""
    blocks = ["# OpenJob", "", f"> {_POSITIONING}", "", faq, "## Posts", ""]
    for post in posts:
        org = post.get("org") or ""
        location = post.get("location") or ""
        blocks.append(f"### {_label(post)}")
        blocks.append(f"Kind: {post.get('kind')}")
        if org:
            blocks.append(f"Organization: {org}")
        if location:
            blocks.append(f"Location: {location}")
        blocks.append(f"Permalink: {post.get('permalink')}")
        blocks.append(f"Excerpt: {post.get('excerpt') or ''}")
        blocks.append("")
    return "\n".join(blocks)


def _rfc822(day: str) -> str:
    try:
        stamp = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        stamp = datetime.now(timezone.utc)
    return format_datetime(stamp)

