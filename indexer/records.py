"""Facts stored for one indexed job. Descriptions are never included."""

from __future__ import annotations

from dataclasses import asdict, dataclass

EMPLOYMENT = (
    "FULL_TIME",
    "PART_TIME",
    "CONTRACTOR",
    "TEMPORARY",
    "INTERN",
    "VOLUNTEER",
    "PER_DIEM",
    "OTHER",
)
REMOTE = ("remote", "onsite", "hybrid", "unspecified")


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    remote: str
    department: str
    employment_type: str
    salary_text: str
    salary_source: str
    posted: str
    updated: str
    deadline: str
    source_url: str
    apply_url: str

    def as_dict(self) -> dict:
        return asdict(self)


def employment(value: object) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    if not text:
        return ""
    if "intern" in text:
        return "INTERN"
    if "part" in text and "time" in text:
        return "PART_TIME"
    if "full" in text and "time" in text or text in {"fulltime", "permanent"}:
        return "FULL_TIME"
    if "contract" in text:
        return "CONTRACTOR"
    if "temp" in text:
        return "TEMPORARY"
    if "volunteer" in text:
        return "VOLUNTEER"
    if "per diem" in text or "perdiem" in text:
        return "PER_DIEM"
    if text in {"other"}:
        return "OTHER"
    return ""


def workplace(value: object, location: str = "") -> str:
    text = f"{value or ''} {location}".lower()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text or "telecomm" in text or "anywhere" in text:
        return "remote"
    if any(word in text for word in ("on-site", "onsite", "on site", "office")):
        return "onsite"
    return "unspecified"


def day(value: object) -> str:
    """Return YYYY-MM-DD from an ISO string or a millisecond timestamp."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        from datetime import datetime, timezone

        stamp = float(value)
        if stamp > 10_000_000_000:
            stamp /= 1000
        return datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return ""


def https(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("https://") and " " not in text:
        return text
    return ""
