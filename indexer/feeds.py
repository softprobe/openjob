"""Turn one public ATS payload into job facts. Description fields are dropped."""

from __future__ import annotations

import json
from typing import Any

from indexer.records import Job, day, employment, https, workplace

FEED_URL = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
    "lever": "https://api.lever.co/v0/postings/{board}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{board}",
}


def feed_url(ats: str, board: str) -> str:
    return FEED_URL[ats].format(board=board)


def parse(ats: str, payload: bytes, *, company: str) -> list[Job]:
    data = json.loads(payload.decode("utf-8"))
    if ats == "greenhouse":
        return _greenhouse(data, company)
    if ats == "lever":
        return _lever(data, company)
    if ats == "ashby":
        return _ashby(data, company)
    if ats == "workable":
        return _workable(data, company)
    raise ValueError(f"Unknown ATS {ats!r}.")


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
