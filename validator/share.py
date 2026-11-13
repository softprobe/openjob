"""Permalinks and share links for a public post.

The prefilled text is the listing, not a way to reach the person. Jobs use the
role, company, and location. Talent uses the headline. Companies use the name
and location. Apply links, profile URLs, phone numbers, and email addresses
are left out, including the documentation allow-list the post checker ignores.
"""

from __future__ import annotations

import html
import re
from typing import Mapping
from urllib.parse import quote, urlencode

from validator.privacy import has_contact_pattern

PAGES_ORIGIN = "https://softprobe.github.io/openjob"
GENERIC = "OpenJob"
HN_TITLE_LIMIT = 80

_URL = re.compile(r"(?i)\b(?:https?://|mailto:|tel:)\S+")
_PLATFORMS = (
    ("linkedin", "LinkedIn"),
    ("x", "X"),
    ("reddit", "Reddit"),
    ("hackernews", "Hacker News"),
    ("facebook", "Facebook"),
    ("telegram", "Telegram"),
    ("whatsapp", "WhatsApp"),
    ("weibo", "Weibo"),
)

_KIND_LABEL = {
    "job": "Job · 职位",
    "talent": "Talent · 人才",
    "talent-ref": "Talent · 人才",
    "company": "Company · 公司",
}
_REMOTE_LABEL = {
    "remote": "Remote · 远程",
    "onsite": "On-site · 到岗",
    "hybrid": "Hybrid · 混合",
}
_FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' fill='%23f3efe4'/%3E%3Crect x='4' y='4' width='24' "
    "height='24' fill='none' stroke='%23b42318' stroke-width='2'/%3E%3C/svg%3E"
)


def permalink(rel: str) -> str:
    slug = _slug(rel)
    return f"{PAGES_ORIGIN}/p/{slug}/"


def share_text(meta: Mapping[str, object]) -> str:
    """Public blurb. Contact fields are not read."""
    kind = meta.get("kind")
    if kind == "job":
        parts = [_clean(meta.get("title")), _clean(meta.get("company_name")), _clean(meta.get("location"))]
    elif kind in {"talent", "talent-ref"}:
        parts = [_clean(meta.get("headline"))]
    elif kind == "company":
        parts = [_clean(meta.get("name")), _clean(meta.get("location"))]
    else:
        parts = []
    text = " — ".join(part for part in parts if part)
    if not text or has_contact_pattern(text):
        return GENERIC
    return text


def card_description(excerpt: str) -> str:
    """Open Graph description. URLs and contact shapes are removed."""
    text = _clean(excerpt)
    if len(text) < 20 or has_contact_pattern(text):
        return "A public post on OpenJob."
    if len(text) > 200:
        return text[:199].rstrip() + "…"
    return text


def share_links(text: str, url: str) -> list[dict[str, str]]:
    """Public share-intent URLs. No SDK and no prefilled contact field."""
    encoded = quote(url, safe="")
    title = hn_title(text)
    message = f"{text}\n{url}"
    hrefs = {
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded}",
        "x": "https://x.com/intent/tweet?" + urlencode({"text": text, "url": url}),
        "reddit": "https://www.reddit.com/submit?" + urlencode({"url": url, "title": text}),
        "hackernews": "https://news.ycombinator.com/submitlink?" + urlencode({"u": url, "t": title}),
        "facebook": "https://www.facebook.com/sharer/sharer.php?" + urlencode({"u": url}),
        "telegram": "https://t.me/share/url?" + urlencode({"url": url, "text": text}),
        "whatsapp": "https://api.whatsapp.com/send?" + urlencode({"text": message}),
        "weibo": "https://service.weibo.com/share/share.php?" + urlencode({"url": url, "title": text}),
    }
    return [{"id": key, "label": label, "href": hrefs[key]} for key, label in _PLATFORMS]


def hn_title(text: str, limit: int = HN_TITLE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    trimmed = text[:limit].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip()
    trimmed = trimmed.rstrip(" —-")
    return trimmed or text[:limit]


def render_share_comment(meta: Mapping[str, object], rel: str) -> str:
    url = permalink(rel)
    text = share_text(meta)
    lines = [
        "<!-- openjob-share -->",
        "Your post is on OpenJob. The permalink is published when this pull request is on `main` and the Pages workflow finishes.",
        "",
        f"**Permalink:** {url}",
        "",
        "The share text below is the public listing only. It has no phone number, no email address, and no apply or profile link.",
        "",
        f"> {text}",
        "",
    ]
    notes = {
        "linkedin": "LinkedIn reads the title and description from the page.",
        "facebook": "Facebook reads the title and description from the page.",
        "hackernews": "Hacker News uses this text, shortened to 80 characters.",
    }
    for item in share_links(text, url):
        note = notes.get(item["id"])
        if note:
            lines.append(f"- [{item['label']}]({item['href']}) — {note}")
        else:
            lines.append(f"- [{item['label']}]({item['href']})")
    lines.extend(
        [
            "",
            f"Copy link: `{url}`",
            "",
            "WeChat has no public share URL. Open the permalink and use the QR code on that page. "
            "The code is drawn in the browser from the permalink.",
            "",
        ]
    )
    return "\n".join(lines)


def render_post_page(post: Mapping[str, object], body: str) -> str:
    """Static permalink page. Crawlers read the meta tags; the buttons are plain links."""
    path = str(post["path"])
    url = str(post["permalink"])
    text = str(post["share_text"])
    description = card_description(str(post.get("excerpt") or ""))
    prefix = _asset_prefix(path)
    kind = str(post["kind"])
    lang = "zh" if _only_zh(post.get("languages")) else "en"
    title = _page_heading(post)
    deck = _page_deck(post)
    e = html.escape
    badges = _badges(post)
    tags = _tags(post.get("tags") or [])
    actions = _actions(post)
    share_anchors = "\n".join(
        f'<a href="{e(item["href"], quote=True)}" rel="noopener noreferrer" target="_blank">{e(item["label"])}</a>'
        for item in post.get("shares") or []
    )
    board = f"{prefix}index.html#{_slug(path)}"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(text)} — OpenJob</title>
  <meta name="description" content="{e(description, quote=True)}">
  <link rel="canonical" href="{e(url, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="OpenJob">
  <meta property="og:title" content="{e(text, quote=True)}">
  <meta property="og:description" content="{e(description, quote=True)}">
  <meta property="og:url" content="{e(url, quote=True)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{e(text, quote=True)}">
  <meta name="twitter:description" content="{e(description, quote=True)}">
  <link rel="icon" href="{_FAVICON}">
  <link rel="stylesheet" href="{prefix}style.css">
</head>
<body class="entry">
  <a class="skip" href="#share">Skip to share</a>
  <div class="wrap">
    <header class="mast">
      <div>
        <p class="kicker">{e(_KIND_LABEL.get(kind, kind))}</p>
        <h1>{e(title)}</h1>
        <p class="deck">{e(deck)}</p>
      </div>
      <div class="mast-side">
        <a href="{prefix}index.html">OpenJob</a>
      </div>
    </header>
    <article>
      <div class="badges">{badges}</div>
      {render_body(body)}
      {tags}
      <div class="links">{actions}<a href="{e(board, quote=True)}">Board · 公告板</a><span class="sub">{e(_dates(post))}</span></div>
      <section class="share" id="share" data-permalink="{e(url, quote=True)}" data-share-text="{e(text, quote=True)}">
        <h2>Share · 分享</h2>
        <p class="share-text">{e(text)}</p>
        <p class="sub">The buttons send this text and the permalink. They do not send an apply link, a phone number, or an email address. 按钮只发送这段文字和本页链接，不含申请链接、电话或邮箱。</p>
        <div class="share-links">
          {share_anchors}
          <button type="button" data-copy data-done="Copied">Copy link</button>
          <button type="button" data-wechat aria-expanded="false">WeChat</button>
        </div>
        <label class="permalink-label">
          <span class="sub">Permalink · 永久链接</span>
          <input class="permalink" readonly value="{e(url, quote=True)}">
        </label>
        <div class="qr-panel" hidden>
          <canvas aria-label="QR code for this permalink"></canvas>
          <p class="sub">Scan with WeChat. The code is drawn in your browser from the permalink. 用微信扫描。二维码由浏览器根据本页链接生成。</p>
        </div>
      </section>
    </article>
    <footer>
      <p>Contact is a link, not a phone number or an email address. Posts are CC BY 4.0. Code is MIT.</p>
    </footer>
  </div>
  <script src="{prefix}vendor/qrcode.js"></script>
  <script src="{prefix}share.js"></script>
</body>
</html>
"""


def render_body(body: str) -> str:
    blocks: list[str] = []
    for chunk in re.split(r"\n\s*\n", body.strip()):
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        heading = re.fullmatch(r"(#{1,3})\s+(.*)", lines[0]) if len(lines) == 1 else None
        if heading:
            level = min(max(len(heading.group(1)), 2), 3)
            blocks.append(f"<h{level}>{html.escape(heading.group(2).strip())}</h{level}>")
            continue
        escaped = "<br>\n".join(html.escape(line) for line in lines)
        blocks.append(f"<p>{escaped}</p>")
    return "\n".join(blocks)


def _clean(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = _URL.sub(" ", value)
    text = text.replace("<", " ").replace(">", " ")
    text = re.sub(r"\s+", " ", text).strip(" \t-—|")
    return text


def _slug(rel: str) -> str:
    slug = rel[:-3] if rel.endswith(".md") else rel
    return slug.strip("/")


def _asset_prefix(rel: str) -> str:
    depth = 1 + len([part for part in _slug(rel).split("/") if part])
    return "../" * depth


def _only_zh(languages: object) -> bool:
    return isinstance(languages, list) and languages == ["zh"]


def _page_heading(post: Mapping[str, object]) -> str:
    kind = post.get("kind")
    if kind == "job":
        return str(post.get("title") or "")
    if kind in {"talent", "talent-ref"}:
        return str(post.get("title") or "")
    return str(post.get("title") or "")


def _page_deck(post: Mapping[str, object]) -> str:
    kind = post.get("kind")
    if kind == "job":
        bits = [str(post.get("org") or ""), str(post.get("location") or "")]
        compensation = str(post.get("compensation") or "")
        text = " — ".join(bit for bit in bits if bit)
        if compensation:
            text = f"{text} · {compensation}" if text else compensation
        return text
    if kind in {"talent", "talent-ref"}:
        return str(post.get("headline") or "")
    return str(post.get("location") or "")


def _badges(post: Mapping[str, object]) -> str:
    kind = str(post.get("kind") or "")
    chips = [_KIND_LABEL.get(kind, kind)]
    remote = str(post.get("remote") or "")
    if remote in _REMOTE_LABEL:
        chips.append(_REMOTE_LABEL[remote])
    languages = post.get("languages") or []
    if isinstance(languages, list):
        chips.extend(str(language) for language in languages)
    if post.get("example"):
        chips.append("Sample · 示例")
    if post.get("federated"):
        chips.append("Own repo · 独立仓库")
    return "".join(f'<span class="badge">{html.escape(chip)}</span>' for chip in chips)


def _tags(tags: object) -> str:
    if not isinstance(tags, list) or not tags:
        return ""
    items = "".join(f"<li>{html.escape(str(tag))}</li>" for tag in tags)
    return f'<ul class="tags">{items}</ul>'


def _actions(post: Mapping[str, object]) -> str:
    kind = str(post.get("kind") or "")
    if kind == "job":
        label = "Apply · 申请"
    elif kind == "company":
        label = "Website · 网站"
    else:
        label = "Profile · 档案"
    links: list[str] = []
    outbound = _https(post.get("url"))
    source = _https(post.get("source_url"))
    if outbound:
        links.append(
            f'<a href="{html.escape(outbound, quote=True)}" rel="noopener noreferrer">{label}</a>'
        )
    if source:
        links.append(
            f'<a href="{html.escape(source, quote=True)}" rel="noopener noreferrer">Source · 源文件</a>'
        )
    return "".join(links)


def _dates(post: Mapping[str, object]) -> str:
    posted = str(post.get("posted") or "")
    expires = post.get("expires")
    if expires:
        return f"Posted {posted} · Expires {expires}"
    return f"Posted {posted}"


def _https(url: object) -> str | None:
    if isinstance(url, str) and url.startswith("https://") and not any(char.isspace() for char in url):
        return url
    return None
