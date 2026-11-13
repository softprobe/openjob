"""Turn Markdown post bodies into plain descriptions.

Parenthetical URLs are removed without eating the next sentence. A bare URL
becomes its host, which is the link text a reader would have seen. Markdown
links keep their label. Truncation stops on a word boundary.
"""

from __future__ import annotations

import re

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:https?://[^)\s]+)\)")
_PAREN_URL = re.compile(r"\s*\(\s*https?://[^)]+\)")
_BARE_URL = re.compile(r"https?://[^\s)]+")
_HEADING = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_MARKDOWN_MARKS = re.compile(r"[#>*_\[\]]")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")
_SPACES = re.compile(r"\s+")


def clean_prose(text: str) -> str:
    """Plain sentence text. Safe to run more than once."""
    if not text:
        return ""
    cleaned = _FENCE.sub(" ", text)
    cleaned = _MD_LINK.sub(r"\1", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = _PAREN_URL.sub("", cleaned)
    cleaned = _BARE_URL.sub(_host_for_url, cleaned)
    cleaned = _HEADING.sub("", cleaned)
    cleaned = _MARKDOWN_MARKS.sub("", cleaned)
    cleaned = _SPACES.sub(" ", cleaned).strip()
    cleaned = _SPACE_BEFORE_PUNCT.sub(r"\1", cleaned)
    return cleaned


def excerpt(body: str, limit: int = 240) -> str:
    text = clean_prose(body)
    if not text:
        return "OpenJob"
    return truncate_words(text, limit)


def truncate_words(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    if limit < 2:
        return text[:limit]
    room = limit - 1
    cut = text[:room]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip(" \t,;:-—")
    if not cut:
        cut = text[:room].rstrip()
    return cut + "…"


def _host_for_url(match: re.Match[str]) -> str:
    raw = match.group(0)
    url = raw.rstrip(".,;:!?")
    trail = raw[len(url) :]
    host = url.split("//", 1)[-1].split("/")[0].split("?")[0].split("#")[0]
    if host.lower().startswith("www."):
        host = host[4:]
    return (host or url) + trail
