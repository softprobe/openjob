"""Sitemap, robots, feeds, llms.txt, and the no-JS homepage list.

The homepage lists the newest posts in each section and links to an archive.
Archive pages partition every live post. ``sitemap.xml`` is a sitemap index.
Feeds and ``llms-full.txt`` keep a newest-first cap so a million posts do not
turn one file into a multi-megabyte download.

``robots.txt`` is written next to the other site files. On a github.io project
site, crawlers request robots.txt from the host root, which this file is not.
It becomes the host file when the board is served from its own domain.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from validator.share import (
    GOOGLE_VERIFICATION_BODY,
    GOOGLE_VERIFICATION_FILE,
    TEMPLATE_ORIGIN,
    bare_host,
    pages_origin,
    social_meta,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "site" / "index.html"
_ABOUT = _REPO_ROOT / "site" / "about" / "index.html"
_POSITIONING = (
    "OpenJob is a job board that lives in a Git repository: you post a role or a profile "
    "with a pull request, people find it on a static page, and the file expires unless someone renews it."
)

# Newest posts on the homepage, per section. The archive pages list the rest.
HOMEPAGE_PER_KIND = 100
# Posts on each archive page. Crawlers follow rel=next from page 1.
ARCHIVE_PAGE_SIZE = 200
FEED_LIMIT = 100
LLMS_FULL_LIMIT = 100
# Sitemap protocol limits. A chunk rotates when either one is reached.
SITEMAP_URL_LIMIT = 50_000
SITEMAP_BYTE_LIMIT = 50 * 1024 * 1024

_SECTIONS = (
    ("job", "jobs", "Jobs"),
    ("talent", "talents", "Talent"),
    ("company", "companies", "Companies"),
)
_SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
_URLSET_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<urlset xmlns="{_SITEMAP_NS}">\n'
)
_URLSET_FOOTER = "</urlset>\n"


def write_discovery(
    site_dir: Path,
    document: dict,
    *,
    homepage_per_kind: int = HOMEPAGE_PER_KIND,
    archive_page_size: int = ARCHIVE_PAGE_SIZE,
    feed_limit: int = FEED_LIMIT,
    llms_full_limit: int = LLMS_FULL_LIMIT,
    sitemap_url_limit: int = SITEMAP_URL_LIMIT,
    sitemap_byte_limit: int = SITEMAP_BYTE_LIMIT,
) -> None:
    if min(homepage_per_kind, archive_page_size, feed_limit, llms_full_limit, sitemap_url_limit, sitemap_byte_limit) < 1:
        raise ValueError("Discovery limits must be at least 1.")
    posts = list(document["posts"])
    generated = str(document.get("generated") or "")
    lastmod = generated[:10] if len(generated) >= 10 else datetime.now(timezone.utc).date().isoformat()
    grouped = _group(posts)
    archive_urls = _write_archives(site_dir, grouped, lastmod, archive_page_size)
    _write_homepage(site_dir, grouped, homepage_per_kind, archive_page_size)
    jobs = grouped["job"]
    (site_dir / "feed.xml").write_text(
        _rss(posts[:feed_limit], "OpenJob", f"{_origin()}/feed.xml"), encoding="utf-8"
    )
    (site_dir / "jobs.xml").write_text(
        _rss(jobs[:feed_limit], "OpenJob jobs", f"{_origin()}/jobs.xml"), encoding="utf-8"
    )
    (site_dir / "atom.xml").write_text(
        _atom(posts[:feed_limit], "OpenJob", f"{_origin()}/atom.xml"), encoding="utf-8"
    )
    (site_dir / "jobs.atom").write_text(
        _atom(jobs[:feed_limit], "OpenJob jobs", f"{_origin()}/jobs.atom"), encoding="utf-8"
    )
    (site_dir / "feed.json").write_text(
        _json_feed(posts[:feed_limit], "OpenJob", f"{_origin()}/feed.json"), encoding="utf-8"
    )
    (site_dir / "jobs.json").write_text(
        _json_feed(jobs[:feed_limit], "OpenJob jobs", f"{_origin()}/jobs.json"), encoding="utf-8"
    )
    (site_dir / "llms.txt").write_text(_llms(grouped), encoding="utf-8")
    (site_dir / "llms-full.txt").write_text(_llms_full(posts, llms_full_limit), encoding="utf-8")
    (site_dir / "robots.txt").write_text(_robots(), encoding="utf-8")
    _write_sitemaps(
        site_dir,
        _sitemap_locs(lastmod, archive_urls, posts),
        lastmod,
        url_limit=sitemap_url_limit,
        byte_limit=sitemap_byte_limit,
    )
    _write_about(site_dir)
    _write_cname(site_dir)
    _write_google_file(site_dir)


def _origin() -> str:
    return pages_origin().rstrip("/")


def _home() -> str:
    return _origin() + "/"


def _with_origin(text: str) -> str:
    live = _origin()
    if live == TEMPLATE_ORIGIN:
        return text
    return text.replace(TEMPLATE_ORIGIN, live)


def _apply_social(text: str) -> str:
    start = "<!-- openjob:social -->"
    end = "<!-- /openjob:social -->"
    if start not in text or end not in text:
        return text
    pre, _, rest = text.partition(start)
    _, _, post = rest.partition(end)
    return f"{pre}{start}\n{social_meta()}\n  {end}{post}"


def _group(posts: list[dict]) -> dict[str, list[dict]]:
    """One pass. Input order is preserved, which is newest first."""
    grouped = {key: [] for key, _slug, _title in _SECTIONS}
    for post in posts:
        grouped[_section_key(post)].append(post)
    return grouped


def _section_key(post: dict) -> str:
    kind = post.get("kind")
    if kind in {"talent", "talent-ref"}:
        return "talent"
    if kind == "company":
        return "company"
    return "job"


def _write_homepage(
    site_dir: Path, grouped: dict[str, list[dict]], per_kind: int, page_size: int
) -> None:
    template = _TEMPLATE.read_text(encoding="utf-8")
    marker = "<!-- openjob:posts -->"
    if marker not in template:
        raise ValueError("site/index.html is missing the <!-- openjob:posts --> marker")
    page = template.replace(marker, _homepage_list(grouped, per_kind, page_size), 1)
    (site_dir / "index.html").write_text(_with_origin(_apply_social(page)), encoding="utf-8")


def _homepage_list(grouped: dict[str, list[dict]], per_kind: int, page_size: int) -> str:
    sections = []
    for key, slug, title in _SECTIONS:
        posts = grouped[key]
        if not posts:
            continue
        items = "\n".join(_post_item(post, "p/" + str(post["path"]).removesuffix(".md") + "/") for post in posts[:per_kind])
        pages = _page_count(len(posts), page_size)
        archive = f"{slug}/page/1/"
        sections.append(
            "\n".join(
                [
                    "<section>",
                    f"<h2>{title}</h2>",
                    "<ul>",
                    items,
                    "</ul>",
                    f'<p><a href="{archive}">{title} archive, {len(posts)} posts</a></p>',
                    "</section>",
                ]
            )
        )
    if not sections:
        return '<p id="post-list">No posts yet.</p>'
    return '<div id="post-list">\n' + "\n".join(sections) + "\n</div>"


def _post_item(post: dict, href: str) -> str:
    return f'<li><a href="{escape(href)}">{escape(_label(post))}</a></li>'


def _write_archives(
    site_dir: Path, grouped: dict[str, list[dict]], lastmod: str, page_size: int
) -> list[tuple[str, str]]:
    """Write archive pages. Return ``(absolute URL, lastmod)`` for the sitemap."""
    urls: list[tuple[str, str]] = []
    for key, slug, title in _SECTIONS:
        directory = site_dir / slug
        if directory.is_symlink():
            raise ValueError(f"Refusing to replace a symlinked archive directory: {slug}")
        if directory.exists():
            shutil.rmtree(directory)
        posts = grouped[key]
        pages = _page_count(len(posts), page_size)
        for number in range(1, pages + 1):
            chunk = posts[(number - 1) * page_size : number * page_size]
            dest = directory / "page" / str(number) / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(
                _archive_page(slug, title, number, pages, chunk),
                encoding="utf-8",
            )
            urls.append((f"{_origin()}/{slug}/page/{number}/", lastmod))
    return urls


def _archive_page(slug: str, title: str, number: int, pages: int, posts: list[dict]) -> str:
    canonical = f"{_origin()}/{slug}/page/{number}/"
    prev_href = f"{_origin()}/{slug}/page/{number - 1}/" if number > 1 else ""
    next_href = f"{_origin()}/{slug}/page/{number + 1}/" if number < pages else ""
    head = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape(title)}, page {number} of {pages} — OpenJob</title>",
        f'<link rel="canonical" href="{escape(canonical)}">',
    ]
    if prev_href:
        head.append(f'<link rel="prev" href="{escape(prev_href)}">')
    if next_href:
        head.append(f'<link rel="next" href="{escape(next_href)}">')
    head.extend(social_meta().splitlines())
    head.extend(
        [
            '<link rel="stylesheet" href="../../../style.css">',
            "</head>",
            "<body>",
            '<div class="wrap">',
            '<header class="mast">',
            "<div>",
            '<p class="kicker"><a href="../../../">OpenJob</a></p>',
            f"<h1>{escape(title)}</h1>",
            "</div>",
            "</header>",
            f'<p class="count">Page {number} of {pages}</p>',
            "<nav>",
        ]
    )
    if prev_href:
        head.append(f'<a rel="prev" href="{escape(prev_href)}">Previous</a>')
    if next_href:
        head.append(f'<a rel="next" href="{escape(next_href)}">Next</a>')
    head.append("</nav>")
    head.append("<ul>")
    head.extend(_post_item(post, str(post["permalink"])) for post in posts)
    head.extend(["</ul>", "</div>", "</body>", "</html>", ""])
    return "\n".join(head)


def _page_count(count: int, page_size: int) -> int:
    if count <= 0:
        return 0
    return (count + page_size - 1) // page_size


def _sitemap_locs(lastmod: str, archive_urls: list[tuple[str, str]], posts: list[dict]):
    yield _home(), lastmod
    yield from archive_urls
    for post in posts:
        posted = str(post.get("posted") or lastmod)
        yield str(post["permalink"]), posted[:10]


def _write_sitemaps(site_dir: Path, locs, lastmod: str, *, url_limit: int, byte_limit: int) -> None:
    for stale in site_dir.glob("sitemap-*.xml"):
        if stale.is_file():
            stale.unlink()
    names: list[str] = []
    index = 0
    handle = None
    count = 0
    size = 0
    footer_bytes = len(_URLSET_FOOTER.encode("utf-8"))

    def open_chunk() -> None:
        nonlocal index, handle, count, size
        index += 1
        name = f"sitemap-{index}.xml"
        handle = (site_dir / name).open("w", encoding="utf-8")
        handle.write(_URLSET_HEADER)
        names.append(name)
        count = 0
        size = len(_URLSET_HEADER.encode("utf-8"))

    def close_chunk() -> None:
        assert handle is not None
        handle.write(_URLSET_FOOTER)
        handle.close()

    open_chunk()
    for loc, modified in locs:
        entry = (
            "  <url>\n"
            f"    <loc>{escape(loc)}</loc>\n"
            f"    <lastmod>{escape(modified)}</lastmod>\n"
            "  </url>\n"
        )
        encoded = len(entry.encode("utf-8"))
        if count > 0 and (count >= url_limit or size + encoded + footer_bytes > byte_limit):
            close_chunk()
            open_chunk()
        assert handle is not None
        handle.write(entry)
        count += 1
        size += encoded
    close_chunk()
    _write_sitemap_index(site_dir, names, lastmod)


def _write_sitemap_index(site_dir: Path, names: list[str], lastmod: str) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<sitemapindex xmlns="{_SITEMAP_NS}">',
    ]
    for name in names:
        lines.extend(
            [
                "  <sitemap>",
                f"    <loc>{escape(f'{_origin()}/{name}')}</loc>",
                f"    <lastmod>{escape(lastmod)}</lastmod>",
                "  </sitemap>",
            ]
        )
    lines.extend(["</sitemapindex>", ""])
    (site_dir / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


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


def _robots() -> str:
    if bare_host():
        note = "# This file is served at the host root, so crawlers use it.\n"
    else:
        note = (
            "# On a github.io project site, crawlers read the host root robots.txt,\n"
            "# not this file. This file applies once the board has its own hostname.\n"
        )
    return note + "User-agent: *\nAllow: /\n\n" + f"Sitemap: {_origin()}/sitemap.xml\n"


def _write_about(site_dir: Path) -> None:
    if not _ABOUT.is_file():
        return
    text = _with_origin(_apply_social(_ABOUT.read_text(encoding="utf-8")))
    dest = site_dir / "about" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def _write_cname(site_dir: Path) -> None:
    path = site_dir / "CNAME"
    host = bare_host()
    if host is None:
        if path.is_file() and not path.is_symlink():
            path.unlink()
        return
    path.write_text(host + "\n", encoding="utf-8")


def _write_google_file(site_dir: Path) -> None:
    (site_dir / GOOGLE_VERIFICATION_FILE).write_text(GOOGLE_VERIFICATION_BODY, encoding="utf-8")


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
        f"    <link>{escape(_home())}</link>\n"
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
        f"  <link href=\"{escape(_home())}\" rel=\"alternate\"/>\n"
        f"  <link href=\"{escape(self_url)}\" rel=\"self\"/>\n"
        f"  <id>{escape(_home())}</id>\n"
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
        "home_page_url": _home(),
        "feed_url": self_url,
        "description": _POSITIONING,
        "items": items,
    }
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def _llms(grouped: dict[str, list[dict]]) -> str:
    lines = [
        "# OpenJob",
        "",
        f"> {_POSITIONING}",
        "",
        "Jobs, talent profiles, and company pages are Markdown files in a public GitHub repository. "
        "There are no accounts and no tracking. Phone numbers are not allowed. A job may show one "
        "hiring address when its domain matches the company website. Jobs last 60 days and talent "
        "profiles last 180 days unless renewed. Company pages do not expire. Expired posts leave "
        f"the index at {_origin()}/index.json.",
        "",
        "## Board",
        "",
    ]
    for key, slug, title in _SECTIONS:
        count = len(grouped[key])
        if count:
            lines.append(f"- {title}: {count}. [Archive]({_origin()}/{slug}/page/1/)")
        else:
            lines.append(f"- {title}: 0")
    lines.extend(
        [
            f"- [Sitemap]({_origin()}/sitemap.xml)",
            "",
            "## Docs",
            "",
            "- [README](https://github.com/softprobe/openjob/blob/main/README.md)",
            "- [Contributing](https://github.com/softprobe/openjob/blob/main/CONTRIBUTING.md)",
            f"- [Live index]({_origin()}/index.json)",
            f"- [About]({_origin()}/about/)",
            "",
        ]
    )
    return "\n".join(lines)


def _llms_full(posts: list[dict], limit: int) -> str:
    shown = posts[:limit]
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
    if len(posts) > limit:
        coverage = (
            f"The board has {len(posts)} live posts. This file includes the newest {limit}. "
            f"Every post is linked from the archives and listed in {_origin()}/sitemap.xml."
        )
    else:
        coverage = f"The board has {len(posts)} live posts. This file includes every one."
    blocks = ["# OpenJob", "", f"> {_POSITIONING}", "", faq, "## Posts", "", coverage, ""]
    for post in shown:
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
