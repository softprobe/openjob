"""One polite request per board. No token and no extra job-detail calls."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from indexer import USER_AGENT
from indexer.feeds import feed_url, parse


def build_request(url: str, etag: str | None = None) -> Request:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    return Request(url, headers=headers)


def fetch_board(source: dict, etag: str | None = None, *, timeout: float = 20) -> dict:
    url = feed_url(source["ats"], source["board"])
    request = build_request(url, etag)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            new_etag = response.headers.get("ETag")
        jobs = [job.as_dict() for job in parse(source["ats"], body, company=source["name"])]
        return {"ok": True, "jobs": jobs, "etag": new_etag}
    except HTTPError as exc:
        if exc.code == 304:
            return {"ok": True, "not_modified": True, "etag": etag}
        return {"ok": False, "status": exc.code}
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeError, ValueError):
        return {"ok": False}
