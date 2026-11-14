"""Permalinks and share links for a public post.

The Pages origin is the Actions variable ``PAGES_ORIGIN`` when that is set.
Otherwise it is the project URL of ``GITHUB_REPOSITORY``, and of ``REPO``
outside Actions. The default is ``https://softprobe.github.io/openjob``.

The prefilled text is the listing, not a way to reach the person. Jobs use the
role, company, and location. Talent uses the headline. Companies use the name
and location. Apply links, profile URLs, phone numbers, and email addresses
are left out, including a job's hiring address and the documentation allow-list
the post checker ignores. A job page still shows that address in How to apply.
"""

from __future__ import annotations

import html
import os
import re
from typing import Mapping
from urllib.parse import quote, urlencode, urlsplit

from validator.constants import REPO
from validator.privacy import has_contact_pattern

# GitHub repo and owner names, lowercased. Pages hostnames are lowercase.
_SLUG = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,98}[a-z0-9])?")
GENERIC = "OpenJob"
HN_TITLE_LIMIT = 80
TEMPLATE_ORIGIN = "https://softprobe.github.io/openjob"
OG_ALT = "OpenJob. Open, privacy-first job board on GitHub"
GOOGLE_SITE_VERIFICATION = "a2xq4xTZGnwkNdS2FSOJ9EGiUwnSmcRUcCAa2CUkiPI"
GOOGLE_VERIFICATION_FILE = "googlea714d55b74530204.html"
GOOGLE_VERIFICATION_BODY = "google-site-verification: googlea714d55b74530204.html\n"
_EMPLOYMENT = {
    "FULL_TIME": "Full-time",
    "PART_TIME": "Part-time",
    "CONTRACTOR": "Contractor",
    "TEMPORARY": "Temporary",
    "INTERN": "Intern",
    "VOLUNTEER": "Volunteer",
    "PER_DIEM": "Per diem",
    "OTHER": "Other",
}
_SALARY_UNIT = {"HOUR": "hour", "DAY": "day", "WEEK": "week", "MONTH": "month", "YEAR": "year"}

_URL = re.compile(r"(?i)\b(?:https?://|mailto:|tel:)\S+")
_BODY_LINK = re.compile(r"https://[A-Za-z0-9._~:/?#\[\]@!$&'*+,;=%-]+")
_MAILTO_HREF = re.compile(
    r"(?i)^mailto:[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?)+$"
)
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


def pages_origin(repository: str | None = None) -> str:
    """Project Pages origin for the repository that is publishing the board.

    An Actions variable ``PAGES_ORIGIN`` wins when this is called with no
    repository argument. Otherwise GitHub Actions sets ``GITHUB_REPOSITORY``
    to ``owner/name``, including on ``pull_request_target``. Outside Actions,
    the origin is ``REPO``.

    ``owner/owner.github.io`` is the site root. Every other repository is
    ``https://owner.github.io/name``.
    """
    if repository is None:
        configured = configured_origin()
        if configured is not None:
            return configured
        repository = os.environ.get("GITHUB_REPOSITORY", "")
    origin = _origin_for(repository.strip())
    if origin is None:
        origin = _origin_for(REPO)
    if origin is None:
        raise RuntimeError(f"REPO {REPO!r} is not an owner/name repository.")
    return origin


def configured_origin() -> str | None:
    """``PAGES_ORIGIN`` with one trailing slash removed, or None when unset."""
    raw = os.environ.get("PAGES_ORIGIN", "").strip()
    if not raw:
        return None
    origin = _public_origin(raw)
    if origin is None:
        raise ValueError(
            "PAGES_ORIGIN must be an https origin such as "
            "https://softprobe.github.io/openjob or https://jobs.example.com."
        )
    return origin


def _public_origin(raw: str) -> str | None:
    parsed = urlsplit(raw.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port:
        return None
    path = parsed.path.rstrip("/")
    if path and not path.startswith("/"):
        return None
    if "//" in path or " " in path:
        return None
    host = parsed.hostname.lower()
    if path:
        return f"https://{host}{path}"
    return f"https://{host}"


def bare_host(origin: str | None = None) -> str | None:
    """Hostname of a custom-domain origin. A github.io URL has no CNAME."""
    parsed = urlsplit(origin if origin is not None else pages_origin())
    if parsed.scheme != "https" or parsed.path not in ("", "/"):
        return None
    host = (parsed.hostname or "").lower()
    if not host or host == "github.io" or host.endswith(".github.io"):
        return None
    return host


def google_site_verification() -> str:
    value = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
    return value or GOOGLE_SITE_VERIFICATION


def bing_site_verification() -> str:
    return os.environ.get("BING_SITE_VERIFICATION", "").strip()


def social_meta(origin: str | None = None) -> str:
    """Open Graph image, Twitter card, and site-verification tags."""
    root = (origin or pages_origin()).rstrip("/")
    image = f"{root}/og.png"
    e = html.escape
    lines = [
        f'<meta property="og:image" content="{e(image, quote=True)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{e(OG_ALT, quote=True)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{e(image, quote=True)}">',
        f'<meta name="twitter:image:alt" content="{e(OG_ALT, quote=True)}">',
        f'<meta name="google-site-verification" content="{e(google_site_verification(), quote=True)}">',
    ]
    bing = bing_site_verification()
    if bing:
        lines.append(f'<meta name="msvalidate.01" content="{e(bing, quote=True)}">')
    return "\n".join(lines)


def _origin_for(repository: str) -> str | None:
    if repository.count("/") != 1:
        return None
    owner, name = (part.strip().lower() for part in repository.split("/", 1))
    if _SLUG.fullmatch(owner) is None or _SLUG.fullmatch(name) is None:
        return None
    if name == f"{owner}.github.io":
        return f"https://{owner}.github.io"
    return f"https://{owner}.github.io/{name}"


# Value at import. permalink() calls pages_origin() so later reads follow
# GITHUB_REPOSITORY. This name stays for code that already imported it.
PAGES_ORIGIN = pages_origin()


def permalink(rel: str) -> str:
    slug = _slug(rel)
    return f"{pages_origin()}/p/{slug}/"


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
    """Open Graph description. Emails are removed. URLs become their host."""
    from validator.prose import clean_prose, truncate_words

    text = clean_prose(excerpt)
    if len(text) < 20 or has_contact_pattern(text):
        return "A public post on OpenJob."
    return truncate_words(text, 200)


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
    apply_how = _apply_section(post)
    logo = _logo_html(post)
    share_anchors = "\n".join(
        f'<a href="{e(item["href"], quote=True)}" rel="noopener noreferrer" target="_blank">{e(item["label"])}</a>'
        for item in post.get("shares") or []
    )
    home = pages_origin().rstrip("/") + "/"
    board = f"{home}#{_slug(path)}"
    description_html = apply_how + render_body(body)
    from validator.jsonld import post_jsonld

    structured = post_jsonld(post, description_html, body)
    company_link = _company_link(post)
    open_jobs = _open_jobs(post)
    facts = _offer_facts(post)
    social = social_meta(home)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(text)} — OpenJob</title>
  <meta name="description" content="{e(description, quote=True)}">
  <link rel="canonical" href="{e(url, quote=True)}">
  <link rel="alternate" type="text/markdown" href="index.md">
  <link rel="describedby" href="{e(home, quote=True)}llms.txt">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="OpenJob">
  <meta property="og:title" content="{e(text, quote=True)}">
  <meta property="og:description" content="{e(description, quote=True)}">
  <meta property="og:url" content="{e(url, quote=True)}">
  {social}
  <meta name="twitter:title" content="{e(text, quote=True)}">
  <meta name="twitter:description" content="{e(description, quote=True)}">
  <link rel="icon" href="{_FAVICON}">
  <link rel="stylesheet" href="{prefix}style.css">
</head>
<body class="entry">
  <a class="skip" href="#share">Skip to share</a>
  <div class="wrap">
    <header class="mast">
      <div class="identity">
        {logo}
        <div>
          <p class="kicker">{e(_KIND_LABEL.get(kind, kind))}</p>
          <h1>{e(title)}</h1>
          <p class="deck">{e(deck)}</p>
        </div>
      </div>
      <div class="mast-side">
        <a href="{e(home, quote=True)}">OpenJob</a>
      </div>
    </header>
    <article>
      {structured}
      {apply_how}
      <div class="badges">{badges}</div>
      {facts}
      {render_body(body)}
      {open_jobs}
      {tags}
      <div class="links">{company_link}{actions}<a href="{e(board, quote=True)}">Board · 公告板</a><span class="sub">{e(_dates(post))}</span></div>
      <section class="share" id="share" data-permalink="{e(url, quote=True)}" data-share-text="{e(text, quote=True)}">
        <h2>Share · 分享</h2>
        <p class="share-text">{e(text)}</p>
        <p class="sub">The buttons send this text and the permalink. They do not send an apply link, a phone number, or an email address. An Apply by email button on this page is not part of this text. 按钮只发送这段文字和本页链接，不含申请链接、电话或邮箱。页面上的「邮件申请」按钮不在这段文字里。</p>
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
      <p>Phone numbers are not allowed. A job may show Apply by email when the address is on the company domain. Share text never includes a phone number or an email. Posts are CC BY 4.0. Code is MIT.</p>
      <p><a href="{e(home, quote=True)}">OpenJob</a> · <a href="{e(home, quote=True)}about/">About</a> · <a href="https://github.com/softprobe/openjob">Source</a></p>
    </footer>
  </div>
  <script src="{prefix}vendor/qrcode.js"></script>
  <script src="{prefix}share.js"></script>
</body>
</html>
"""


def _company_link(post: Mapping[str, object]) -> str:
    href = post.get("company_permalink")
    name = post.get("org")
    if post.get("kind") != "job" or not isinstance(href, str) or not href or not name:
        return ""
    return (
        f'<a href="{html.escape(href, quote=True)}">{html.escape(str(name))}</a>'
    )


def _open_jobs(post: Mapping[str, object]) -> str:
    jobs = post.get("open_jobs")
    if post.get("kind") != "company" or not isinstance(jobs, list) or not jobs:
        return ""
    items = []
    for job in jobs:
        if not isinstance(job, Mapping):
            continue
        href = job.get("permalink")
        title = job.get("title")
        if not isinstance(href, str) or not isinstance(title, str):
            continue
        items.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(title)}</a></li>')
    if not items:
        return ""
    more = post.get("open_jobs_more")
    more_html = ""
    if isinstance(more, int) and more > 0:
        archive = html.escape(pages_origin().rstrip("/") + "/jobs/page/1/", quote=True)
        more_html = (
            f'<p><a href="{archive}">The jobs archive lists every open role.</a></p>'
        )
    return '<section class="open-jobs"><h2>Open jobs</h2><ul>' + "".join(items) + "</ul>" + more_html + "</section>"


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
        rendered = "<br>\n".join(_inline(line) for line in lines)
        blocks.append(f"<p>{rendered}</p>")
    return "\n".join(blocks)


def _inline(line: str) -> str:
    """Escape a paragraph line, keep `code` as text, and turn https URLs into links."""
    parts = re.split(r"(`[^`\n]+`)", line)
    rendered: list[str] = []
    for part in parts:
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            rendered.append(f"<code>{html.escape(part[1:-1])}</code>")
        else:
            rendered.append(_linkify(part))
    return "".join(rendered)


def _linkify(text: str) -> str:
    pieces: list[str] = []
    cursor = 0
    for match in _BODY_LINK.finditer(text):
        pieces.append(html.escape(text[cursor:match.start()]))
        raw = match.group(0)
        url = raw.rstrip(".,);]}>\"'")
        if len(url) < 12:
            pieces.append(html.escape(raw))
            cursor = match.end()
            continue
        href = html.escape(url, quote=True)
        pieces.append(f'<a href="{href}" rel="noopener noreferrer">{html.escape(url)}</a>')
        pieces.append(html.escape(raw[len(url):]))
        cursor = match.end()
    pieces.append(html.escape(text[cursor:]))
    return "".join(pieces)


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


def _employment_list(value: object) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    return []


def _salary_label(salary: object) -> str:
    if not isinstance(salary, Mapping):
        return ""
    unit = _SALARY_UNIT.get(str(salary.get("unit") or ""))
    currency = salary.get("currency")
    minimum = _amount(salary.get("min"))
    if not unit or not isinstance(currency, str) or not minimum:
        return ""
    maximum = _amount(salary.get("max"))
    amount = f"{minimum}–{maximum}" if maximum else minimum
    return f"{currency} {amount} / {unit}"


def _amount(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return format(value, "g")


def _location_label(place: object) -> str:
    if not isinstance(place, Mapping):
        return ""
    parts = [place.get("city"), place.get("region"), place.get("country")]
    return ", ".join(str(part) for part in parts if isinstance(part, str) and part)


def _offer_facts(post: Mapping[str, object]) -> str:
    if post.get("kind") != "job":
        return ""
    items = []
    pay = _salary_label(post.get("salary"))
    if pay:
        items.append(pay)
    locations = post.get("locations")
    if isinstance(locations, list):
        items.extend(label for label in (_location_label(place) for place in locations) if label)
    if not items:
        return ""
    lis = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f'<ul class="facts">{lis}</ul>'


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
    if kind == "job":
        for code in _employment_list(post.get("employment_type")):
            chips.append(_EMPLOYMENT.get(code, code))
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


def _apply_section(post: Mapping[str, object]) -> str:
    """Hiring instructions at the top of a job page. Share text stays free of them."""
    if post.get("kind") != "job":
        return ""
    https_apply = _https(post.get("apply"))
    mailto = _mailto(post.get("apply_email"))
    address = mailto.split(":", 1)[1] if mailto else ""
    if not https_apply and not address:
        return ""
    buttons: list[str] = []
    if address and mailto:
        buttons.append(
            f'<a href="{html.escape(mailto, quote=True)}" rel="nofollow noopener noreferrer">'
            "Apply by email · 邮件申请</a>"
        )
        buttons.append(
            f'<button type="button" data-copy-email="{html.escape(address, quote=True)}" '
            'data-done="Copied · 已复制">Copy email · 复制邮箱</button>'
        )
    if https_apply:
        buttons.append(
            f'<a href="{html.escape(https_apply, quote=True)}" rel="noopener noreferrer">'
            "Apply · 申请</a>"
        )
    address_html = f'<p class="apply-address">{html.escape(address)}</p>' if address else ""
    return (
        '<section class="apply-how" id="apply">'
        "<h2>How to apply · 如何申请</h2>"
        f"{address_html}"
        f'<div class="apply-actions">{"".join(buttons)}</div>'
        "</section>"
    )


def _actions(post: Mapping[str, object]) -> str:
    kind = str(post.get("kind") or "")
    links: list[str] = []
    if kind == "job":
        https_apply = _https(post.get("apply"))
        mailto = _mailto(post.get("apply_email"))
        if https_apply:
            links.append(
                f'<a href="{html.escape(https_apply, quote=True)}" rel="noopener noreferrer">Apply · 申请</a>'
            )
        if mailto:
            links.append(
                f'<a href="{html.escape(mailto, quote=True)}" rel="nofollow noopener noreferrer">Apply by email · 邮件申请</a>'
            )
    else:
        if kind == "company":
            label = "Website · 网站"
        else:
            label = "Profile · 档案"
        outbound = _https(post.get("url"))
        if outbound:
            links.append(
                f'<a href="{html.escape(outbound, quote=True)}" rel="noopener noreferrer">{label}</a>'
            )
    source = _https(post.get("source_url"))
    if source:
        links.append(
            f'<a href="{html.escape(source, quote=True)}" rel="noopener noreferrer">Source · 源文件</a>'
        )
    return "".join(links)


def _logo_html(post: Mapping[str, object]) -> str:
    kind = post.get("kind")
    if kind not in {"company", "job"}:
        return ""
    url = _https(post.get("logo"))
    if not url:
        return ""
    if kind == "job":
        name = str(post.get("org") or post.get("title") or "Company")
    else:
        name = str(post.get("title") or "Company")
    alt = html.escape(name, quote=True)
    src = html.escape(url, quote=True)
    return (
        f'<img class="logo" src="{src}" alt="{alt}" width="48" height="48" '
        f'referrerpolicy="no-referrer">'
    )


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


def _mailto(url: object) -> str | None:
    if isinstance(url, str) and _MAILTO_HREF.fullmatch(url):
        return url
    return None
