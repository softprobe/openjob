"""Turn one public ATS payload into job facts. Description fields are dropped."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote, urlencode, urlsplit

from indexer.records import Job, day, employment, https, workplace

FEED_URL = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
    "lever": "https://api.lever.co/v0/postings/{board}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{board}",
}
MOKA_PAGE_SIZE = 100
MOKA_MAX_JOBS = 10_000
_MOKA_SITE = re.compile(r"^/(social|campus)-recruitment/([A-Za-z0-9_-]+)/([0-9]+)/?$")


def feed_url(ats: str, board: str, *, website: str | None = None, offset: int = 0) -> str:
    if ats == "moka":
        mode, org, site = moka_site(website, board)
        query = urlencode(
            {
                "mode": mode,
                "siteId": site,
                "status": "open",
                "limit": MOKA_PAGE_SIZE,
                "offset": offset,
            }
        )
        return f"https://api.mokahr.com/api-platform/v1/jobs/{quote(org, safe='')}?{query}"
    return FEED_URL[ats].format(board=board)


def parse(ats: str, payload: bytes, *, company: str, source: dict | None = None) -> list[Job]:
    data = json.loads(payload.decode("utf-8"))
    if ats == "greenhouse":
        return _greenhouse(data, company)
    if ats == "lever":
        return _lever(data, company)
    if ats == "ashby":
        return _ashby(data, company)
    if ats == "workable":
        return _workable(data, company)
    if ats == "moka":
        if source is None:
            raise ValueError("A Moka source record is required to build public job links.")
        return _moka(data, company, source)
    raise ValueError(f"Unknown ATS {ats!r}.")


def moka_site(website: str | None, board: str) -> tuple[str, str, str]:
    """Read the fixed public career-page route used to scope a Moka feed."""
    if not website:
        raise ValueError("A Moka source needs its public career website.")
    parts = urlsplit(website)
    match = _MOKA_SITE.fullmatch(parts.path)
    if (
        parts.scheme != "https"
        or parts.hostname != "app.mokahr.com"
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or match is None
    ):
        raise ValueError("Moka websites must use an app.mokahr.com social or campus recruitment page.")
    mode, org, site = match.groups()
    if org != board:
        raise ValueError("The Moka board identifier must match the career page organization.")
    return mode, org, site


def _greenhouse(data: dict, company: str) -> list[Job]:
    jobs = []
    for item in data.get("jobs") or []:
        if not isinstance(item, dict):
            continue
        location = _name(item.get("location"))
        departments = item.get("departments") or []
        department = _name(departments[0]) if departments else ""
        url = https(item.get("absolute_url"))
        jobs.append(
            Job(
                id=str(item.get("id") or ""),
                title=_text(item.get("title")),
                company=_text(item.get("company_name")) or company,
                location=location,
                remote=workplace("", location),
                department=department,
                employment_type=employment(item.get("employment_type") or _metadata(item, "employment type")),
                salary_text=_text(_metadata(item, "salary") or item.get("salary")),
                salary_source="greenhouse" if _metadata(item, "salary") or item.get("salary") else "",
                posted=day(item.get("first_published")),
                updated=day(item.get("updated_at")),
                deadline=day(item.get("application_deadline")),
                source_url=url,
                apply_url=url,
            )
        )
    return [job for job in jobs if job.id and job.title and job.source_url]


def _lever(data: Any, company: str) -> list[Job]:
    rows = data if isinstance(data, list) else []
    jobs = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        categories = item.get("categories") if isinstance(item.get("categories"), dict) else {}
        location = _text(categories.get("location"))
        salary = item.get("salaryRange") if isinstance(item.get("salaryRange"), dict) else {}
        salary_text = _salary_range(salary) or _text(item.get("salaryDescription"))
        url = https(item.get("hostedUrl"))
        apply = https(item.get("applyUrl")) or url
        jobs.append(
            Job(
                id=_text(item.get("id")),
                title=_text(item.get("text")),
                company=company,
                location=location,
                remote=workplace(item.get("workplaceType"), location),
                department=_text(categories.get("team")),
                employment_type=employment(categories.get("commitment")),
                salary_text=salary_text,
                salary_source="lever" if salary_text else "",
                posted=day(item.get("createdAt")),
                updated="",
                deadline="",
                source_url=url,
                apply_url=apply,
            )
        )
    return [job for job in jobs if job.id and job.title and job.source_url]


def _ashby(data: dict, company: str) -> list[Job]:
    jobs = []
    for item in data.get("jobs") or []:
        if not isinstance(item, dict) or item.get("isListed") is False:
            continue
        location = _text(item.get("location"))
        compensation = item.get("compensation") if isinstance(item.get("compensation"), dict) else {}
        salary_text = _text(compensation.get("scrapeableCompensationSalarySummary"))
        url = https(item.get("jobUrl"))
        apply = https(item.get("applyUrl")) or url
        jobs.append(
            Job(
                id=_text(item.get("id")),
                title=_text(item.get("title")),
                company=company,
                location=location,
                remote=workplace(item.get("workplaceType"), location),
                department=_text(item.get("department")),
                employment_type=employment(item.get("employmentType")),
                salary_text=salary_text,
                salary_source="ashby" if salary_text else "",
                posted=day(item.get("publishedAt")),
                updated="",
                deadline="",
                source_url=url,
                apply_url=apply,
            )
        )
    return [job for job in jobs if job.id and job.title and job.source_url]


def _workable(data: dict, company: str) -> list[Job]:
    name = _text(data.get("name")) or company
    jobs = []
    for item in data.get("jobs") or []:
        if not isinstance(item, dict):
            continue
        location = ", ".join(
            part for part in (_text(item.get("city")), _text(item.get("state")), _text(item.get("country"))) if part
        )
        url = https(item.get("url"))
        apply = https(item.get("application_url")) or url
        remote = "remote" if item.get("telecommuting") is True else workplace("", location)
        jobs.append(
            Job(
                id=_text(item.get("shortcode")),
                title=_text(item.get("title")),
                company=name,
                location=location,
                remote=remote,
                department=_text(item.get("department")),
                employment_type=employment(item.get("employment_type")),
                salary_text="",
                salary_source="",
                posted=day(item.get("published_on")),
                updated="",
                deadline="",
                source_url=url,
                apply_url=apply,
            )
        )
    return [job for job in jobs if job.id and job.title and job.source_url]


def _moka(data: dict, company: str, source: dict) -> list[Job]:
    mode, org, site = moka_site(source.get("website"), source.get("board", ""))
    listing_url = source["website"].rstrip("/")
    application_kind = "campus_apply" if mode == "campus" else "apply"
    apply_root = f"https://app.mokahr.com/{application_kind}/{quote(org, safe='')}/{quote(site, safe='')}"
    jobs = []
    for item in data.get("jobs") or []:
        if not isinstance(item, dict) or _text(item.get("status")).lower() != "open":
            continue
        job_id = _text(item.get("id"))
        title = _text(item.get("title"))
        if not job_id or not title:
            continue
        encoded_id = quote(job_id, safe="")
        locations = _moka_location(item.get("locations"))
        location_text = locations.lower()
        remote = "remote" if any(word in location_text for word in ("remote", "远程", "居家")) else workplace("", locations)
        jobs.append(
            Job(
                id=job_id,
                title=title,
                company=company,
                location=locations,
                remote=remote,
                department=_name(item.get("department")),
                employment_type=_moka_employment(item.get("commitment")),
                salary_text="",
                salary_source="",
                posted=day(item.get("publishedAt") or item.get("openedAt")),
                updated=day(item.get("updatedAt") or item.get("createdAt")),
                deadline="",
                source_url=f"{listing_url}#/job/{encoded_id}",
                apply_url=f"{apply_root}#/job/{encoded_id}/apply?pure=1",
            )
        )
    return jobs


def _moka_location(value: object) -> str:
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return _text(value)
    places = []
    for item in value:
        if not isinstance(item, dict):
            continue
        parts = []
        for key in ("city", "province", "country"):
            part = _text(item.get(key))
            if part and part not in parts:
                parts.append(part)
        if parts:
            place = ", ".join(parts)
            if place not in places:
                places.append(place)
    return "; ".join(places)


def _moka_employment(value: object) -> str:
    text = _text(value).lower()
    if "实习" in text or "intern" in text:
        return "INTERN"
    if "兼职" in text or "part time" in text or "part-time" in text:
        return "PART_TIME"
    if "全职" in text or "full time" in text or "full-time" in text:
        return "FULL_TIME"
    if "合同" in text or "contract" in text:
        return "CONTRACTOR"
    return employment(value)


def _metadata(item: dict, label: str) -> str:
    for entry in item.get("metadata") or []:
        if not isinstance(entry, dict):
            continue
        name = _text(entry.get("name")).lower()
        if label in name:
            return _text(entry.get("value"))
    return ""


def _salary_range(salary: dict) -> str:
    minimum = salary.get("min")
    maximum = salary.get("max")
    currency = _text(salary.get("currency"))
    if minimum in (None, "") and maximum in (None, ""):
        return ""
    interval = salary.get("interval")
    parts = [str(part) for part in (minimum, maximum) if part not in (None, "")]
    text = "-".join(parts)
    if currency:
        text = f"{text} {currency}"
    if interval:
        text = f"{text} / {interval}"
    return text.strip()


def _name(value: object) -> str:
    if isinstance(value, dict):
        return _text(value.get("name"))
    return _text(value)


def _text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())
