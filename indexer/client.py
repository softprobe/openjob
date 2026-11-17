"""One polite request per board. No token and no extra job-detail calls."""

from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from indexer import USER_AGENT
from indexer.feeds import MOKA_MAX_JOBS, MOKA_PAGE_SIZE, feed_url, parse


def build_request(url: str, etag: str | None = None) -> Request:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    return Request(url, headers=headers)


def fetch_board(source: dict, etag: str | None = None, *, timeout: float = 20) -> dict:
    if source["ats"] == "moka":
        return _fetch_moka(source, etag, timeout=timeout)
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


def _fetch_moka(source: dict, etag: str | None, *, timeout: float) -> dict:
    jobs = []
    first_etag = None
    offset = 0
    try:
        while True:
            if offset:
                time.sleep(0.25)
            url = feed_url("moka", source["board"], website=source.get("website"), offset=offset)
            request = build_request(url, etag if offset == 0 else None)
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
                if offset == 0:
                    first_etag = response.headers.get("ETag")
            page = json.loads(body.decode("utf-8"))
            if not isinstance(page, dict) or page.get("code") not in (None, 0, "0", 200, "200"):
                return {"ok": False}
            page_jobs = page.get("jobs")
            if not isinstance(page_jobs, list):
                return {"ok": False}
            if offset == 0:
                total = int(page.get("total", len(page_jobs)))
                if total < 0 or total > MOKA_MAX_JOBS:
                    return {"ok": False}
            jobs.extend(
                job.as_dict()
                for job in parse("moka", body, company=source["name"], source=source)
            )
            if total == 0 or offset + len(page_jobs) >= total:
                break
            if not page_jobs:
                return {"ok": False}
            offset += len(page_jobs)
        unique = {job["id"]: job for job in jobs}
        return {"ok": True, "jobs": list(unique.values()), "etag": first_etag}
    except HTTPError as exc:
        if exc.code == 304:
            return {"ok": True, "not_modified": True, "etag": etag}
        return {"ok": False, "status": exc.code}
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeError, ValueError):
        return {"ok": False}
