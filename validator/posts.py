"""Load a post and check schema, path, size, privacy, links, and dates."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

from validator.constants import (
    BINARY_FIXTURE_ALLOWLIST,
    FUTURE_SKEW_DAYS,
    JOB_DAYS,
    KIND_ROOT,
    MAX_LINKS,
    MAX_POST_BYTES,
    MIN_BODY_CHARS,
    NEW_POST_MAX_AGE_DAYS,
    POST_ROOTS,
    TALENT_DAYS,
)
from validator.issues import FIX, Issue
from validator.privacy import find_contacts

BINARY_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".pdf",
        ".zip",
        ".gz",
        ".tgz",
        ".tar",
        ".7z",
        ".rar",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".mp3",
        ".mp4",
        ".mov",
        ".avi",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".wasm",
        ".exe",
        ".dmg",
        ".heic",
        ".bmp",
        ".tif",
        ".tiff",
        ".avif",
        ".psd",
        ".ai",
        ".apk",
        ".ipa",
        ".bin",
        ".so",
        ".dylib",
        ".class",
        ".jar",
        ".pyc",
    }
)
MAGIC = (
    (b"%PDF", "pdf"),
    (b"\x89PNG", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"PK\x03\x04", "zip"),
    (b"\x7fELF", "elf"),
    (b"RIFF", "riff"),
)

SHORTENERS = frozenset(
    {
        "bit.ly",
        "bitly.com",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "adf.ly",
        "cutt.ly",
        "rb.gy",
        "shorturl.at",
        "tiny.cc",
        "rebrand.ly",
        "t.ly",
        "lnkd.in",
        "db.tt",
        "tr.im",
        "v.gd",
        "t.cn",
        "url.cn",
        "dwz.cn",
        "suo.im",
    }
)

JOB_PATH = re.compile(r"^jobs/(\d{4})/(\d{2})/([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TALENT_PATH = re.compile(
    r"^talents/([a-z0-9])/([a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,38})\.md$"
)
COMPANY_PATH = re.compile(r"^companies/([a-z0-9])/([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROFILE_URL = re.compile(
    r"^https://(?:github\.com|raw\.githubusercontent\.com)/([A-Za-z0-9-]+)/openjob-profile(?:/.*)?$"
)
BODY_URL = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)
DANGEROUS_URL = re.compile(r"(?i)\b(?:javascript|data|vbscript):")


def is_post_path(rel: str) -> bool:
    return rel.startswith(tuple(f"{root}/" for root in POST_ROOTS)) and rel.endswith(".md")


def is_post_tree(rel: str) -> bool:
    return rel.startswith(tuple(f"{root}/" for root in POST_ROOTS))


def binary_issues(path: Path, rel: str) -> list[Issue]:
    """Report binaries. Callers decide whether a fixture path is exempt."""
    issues: list[Issue] = []
    suffix = path.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        issues.append(
            Issue(
                "binary",
                rel,
                f"`{rel}` is a `{suffix}` file. Posts are Markdown text.",
                FIX["binary"],
            )
        )
        return issues
    try:
        data = path.read_bytes() if not path.is_symlink() else b""
    except OSError:
        return issues
    if b"\x00" in data[:8192]:
        issues.append(Issue("binary", rel, f"`{rel}` contains binary data.", FIX["binary"]))
        return issues
    for magic, label in MAGIC:
        if data.startswith(magic):
            issues.append(
                Issue(
                    "binary",
                    rel,
                    f"`{rel}` looks like a {label} file.",
                    FIX["binary"],
                )
            )
            return issues
    return issues


def exempt_binary(rel: str) -> bool:
    return rel in BINARY_FIXTURE_ALLOWLIST


def iter_post_files(root: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for folder in POST_ROOTS:
        base = root / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() or path.is_symlink():
                found.append((path.relative_to(root).as_posix(), path))
    return found


def validate_tree(root: Path, *, today: date | None = None) -> list[Issue]:
    today = today or _utc_today()
    issues: list[Issue] = []
    for rel, path in iter_post_files(root):
        if not rel.endswith(".md"):
            issues.extend(_binary_or_type(path, rel))
            continue
        issues.extend(validate_post(root=root, rel=rel, today=today))
    return issues


def validate_post(
    *,
    root: Path,
    rel: str,
    today: date,
    author: str | None = None,
    maintainers: set[str] | None = None,
    base_meta: dict | None = None,
    new_file: bool = False,
) -> list[Issue]:
    path = root / rel
    issues = _structural(path, rel)
    if any(issue.code in {"binary", "symlink", "oversize", "encoding"} for issue in issues):
        # Oversize text is still scanned for contact details so one push shows both.
        if not any(issue.code in {"binary", "symlink", "encoding"} for issue in issues):
            text = _read_text(path)
            if text is not None:
                issues.extend(_privacy_issues(text, rel))
        return issues

    text = _read_text(path)
    if text is None:
        return issues + [Issue("encoding", rel, "The file is not valid UTF-8.", FIX["encoding"])]
    try:
        meta, body = parse_post(text)
    except PostParseError as exc:
        issues.extend(_privacy_issues(text, rel))
        issues.append(Issue("front-matter", rel, str(exc), FIX["front-matter"]))
        return issues

    scan_text = text
    hiring_issues: list[Issue] = []
    if meta.get("kind") == "job":
        scan_text, hiring_issues = _prepare_hiring_email(text, meta, root=root, rel=rel)
    issues.extend(_privacy_issues(scan_text, rel))
    issues.extend(hiring_issues)
    issues.extend(_schema_issues(meta, rel))
    issues.extend(_path_issues(rel, meta))
    issues.extend(_body_issues(body, rel))
    issues.extend(_link_issues(meta, body, rel))
    issues.extend(_date_issues(meta, today=today, new_file=new_file, base_meta=base_meta, rel=rel))
    issues.extend(_federated_issues(meta, rel))
    if author is not None:
        issues.extend(
            _ownership_issues(
                meta,
                rel=rel,
                author=author,
                base_meta=base_meta,
            )
        )
        issues.extend(
            _example_issues(
                meta,
                rel=rel,
                author=author,
                maintainers=maintainers or set(),
                base_meta=base_meta,
            )
        )
    return issues


class PostParseError(ValueError):
    pass


def parse_post(text: str) -> tuple[dict, str]:
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        raise PostParseError("The file does not start with YAML front matter.")
    marker = "\n---"
    end = text.find(marker, 3)
    if end == -1:
        raise PostParseError("The front matter is missing its closing `---` line.")
    raw = text[text.find("\n") + 1 : end]
    body = text[end + len(marker) :]
    if body.startswith("\n"):
        body = body[1:]
    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise PostParseError(f"The YAML front matter could not be parsed: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PostParseError("The front matter must be a YAML mapping of fields.")
    return _canon(loaded), body


def load_post(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    return parse_post(text)


def effective_expiry(meta: dict) -> date | None:
    """Last day the post stays on the board, or None when it does not expire."""
    if meta.get("example") is True:
        return None
    kind = meta.get("kind")
    if kind == "company":
        return None
    posted = _maybe_date(meta.get("posted"))
    if posted is None or kind not in {"job", "talent", "talent-ref"}:
        return None
    renewed = _maybe_date(meta.get("renewed")) if meta.get("renewed") else None
    start = renewed or posted
    days = JOB_DAYS if kind == "job" else TALENT_DAYS
    explicit = _maybe_date(meta.get("expires")) if meta.get("expires") else None
    if explicit is not None:
        return explicit
    return start + timedelta(days=days)


def is_expired(meta: dict, today: date) -> bool:
    expires = effective_expiry(meta)
    return expires is not None and expires < today


def owner_of(meta: dict) -> str:
    kind = meta.get("kind")
    if kind in {"talent", "talent-ref"}:
        value = meta.get("github")
    else:
        value = meta.get("posted_by")
    return value.lower() if isinstance(value, str) else ""


def maintainers_from(root: Path) -> set[str]:
    path = root / ".github" / "CODEOWNERS"
    owners: set[str] = set()
    if path.is_file() and not path.is_symlink():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.split("#", 1)[0].strip()
            if not stripped:
                continue
            for token in stripped.split()[1:]:
                if token.startswith("@") and len(token) > 1:
                    owners.add(token[1:].lower())
    # Person who maintains the board when CODEOWNERS is missing. Not the repo owner.
    return owners or {"zwobill"}


def _structural(path: Path, rel: str) -> list[Issue]:
    if path.is_symlink():
        return [Issue("symlink", rel, "Symlinks are not allowed.", FIX["symlink"])]
    if not path.is_file():
        return [Issue("bad-path", rel, "The post file is missing.", FIX["bad-path"])]
    binary = binary_issues(path, rel)
    if binary:
        return binary
    size = path.stat().st_size
    issues: list[Issue] = []
    if size > MAX_POST_BYTES:
        issues.append(
            Issue(
                "oversize",
                rel,
                f"The file is {size} bytes. The limit is {MAX_POST_BYTES} bytes (10 KB).",
                FIX["oversize"],
            )
        )
    return issues


def _binary_or_type(path: Path, rel: str) -> list[Issue]:
    if exempt_binary(rel):
        return []
    found = binary_issues(path, rel)
    if found:
        return found
    return [
        Issue(
            "bad-path",
            rel,
            "Only Markdown posts belong under jobs/, talents/, and companies/.",
            FIX["bad-path"],
        )
    ]


def _read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


_MAILTO_VALUE = re.compile(
    r"(?i)^mailto:([A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?)+)$"
)
_HIRING_FIX = (
    "Put one hiring address in `apply` (`mailto:jobs@company.example`) or in `apply_email`, "
    "and only when its domain matches the company website (`www.` is ignored). "
    "The company page is the source when that page exists; otherwise set `website` on the job. "
    "Remove every other email, including the body. Talent posts cannot include an email. "
    "Phone numbers are never allowed."
)


def job_contact_links(meta: dict) -> tuple[str | None, str | None]:
    """Return ``(https apply link, mailto hiring address)`` for a job."""
    https_apply: str | None = None
    mailto: str | None = None
    apply = meta.get("apply")
    if isinstance(apply, str) and apply.startswith("https://"):
        https_apply = apply
    elif isinstance(apply, str) and _mailto_address(apply):
        mailto = apply.strip()
    apply_email = meta.get("apply_email")
    if isinstance(apply_email, str) and _mailto_address(apply_email):
        mailto = apply_email.strip()
    return https_apply, mailto


def company_website(root: Path, meta: dict) -> str | None:
    """Website whose domain a hiring address must match.

    A company page wins when the file exists, so a job cannot point `website`
    at a freemail host while its company page says otherwise. With no company
    page, the job's own `website` is the source.
    """
    page = _company_page_path(root, meta.get("company"))
    if page is not None:
        return _read_website(page)
    own = meta.get("website")
    if isinstance(own, str) and own.startswith("https://") and not any(char.isspace() for char in own):
        return own
    return None


def _prepare_hiring_email(
    text: str,
    meta: dict,
    *,
    root: Path,
    rel: str,
) -> tuple[str, list[Issue]]:
    """Allow one matching-domain hiring address in ``apply`` or ``apply_email``.

    The field is removed from the text the generic scanner sees. A copy in the
    body, a second address, a mismatched domain, and every talent email stay
    visible to that scanner or become their own issue. Phone numbers are untouched.
    """
    slots = _hiring_slots(meta)
    if not slots:
        return text, []
    issues: list[Issue] = []
    if len(slots) > 1:
        issues.append(
            Issue(
                "privacy-email",
                rel,
                "A job can name one hiring address, in `apply` or in `apply_email`, not both.",
                _HIRING_FIX,
            )
        )
    website = company_website(root, meta)
    host = _website_host(website) if website else None
    for field, _raw, address in slots:
        domain = _email_domain(address)
        if host and domain and _domains_match(domain, host):
            continue
        if host is None or domain is None:
            message = (
                f"The hiring address in `{field}` is only allowed when its domain matches "
                "a company website. Add `website` on the company page, or on the job when "
                "there is no company page."
            )
        else:
            message = (
                f"The hiring address in `{field}` uses `{domain}`, which does not match "
                f"the company website domain `{host}`."
            )
        issues.append(Issue("privacy-email", rel, message, _HIRING_FIX))
    parts = _split_front_matter(text)
    if parts is None:
        return text, issues
    front, rest = parts
    for field, raw, _address in slots:
        front = _neutralize_mailto_field(front, field, raw)
    return front + rest, issues


def _hiring_slots(meta: dict) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for field in ("apply", "apply_email"):
        raw = meta.get(field)
        address = _mailto_address(raw)
        if isinstance(raw, str) and address:
            found.append((field, raw.strip(), address))
    return found


def _mailto_address(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = _MAILTO_VALUE.fullmatch(value.strip())
    if match is None:
        return None
    return match.group(1)


def _website_host(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    host = parsed.hostname.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if "." not in host or not host:
        return None
    return host


def _email_domain(address: str) -> str | None:
    domain = address.rsplit("@", 1)[-1].lower().rstrip(".")
    if "." not in domain or domain.startswith(".") or ".." in domain:
        return None
    return domain


def _domains_match(email_domain: str, site_host: str) -> bool:
    """True when the two hosts are equal, or one is a subdomain of the other."""
    email_labels = email_domain.split(".")
    site_labels = site_host.split(".")
    if len(email_labels) < 2 or len(site_labels) < 2:
        return False
    if email_labels == site_labels:
        return True
    if len(site_labels) > len(email_labels) and site_labels[-len(email_labels) :] == email_labels:
        return True
    if len(email_labels) > len(site_labels) and email_labels[-len(site_labels) :] == site_labels:
        return True
    return False


def _company_page_path(root: Path, company: object) -> Path | None:
    if not isinstance(company, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", company):
        return None
    path = root / "companies" / company[0] / f"{company}.md"
    if path.is_file() and not path.is_symlink():
        return path
    return None


def _read_website(path: Path) -> str | None:
    try:
        meta, _body = load_post(path)
    except (OSError, PostParseError, UnicodeError):
        return None
    website = meta.get("website")
    if isinstance(website, str) and website.startswith("https://") and not any(char.isspace() for char in website):
        return website
    return None


def _split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    marker = "\n---"
    end = text.find(marker, 3)
    if end == -1:
        return None
    return text[: end + len(marker)], text[end + len(marker) :]


def _neutralize_mailto_field(front: str, field: str, raw_value: str) -> str:
    lines = front.splitlines(keepends=True)
    replaced = False
    out: list[str] = []
    for line in lines:
        if not replaced and _line_is_field(line, field, raw_value):
            newline = "\n" if line.endswith("\n") else ""
            out.append(f"{field}: https://example.com/hiring-contact{newline}")
            replaced = True
        else:
            out.append(line)
    if replaced:
        return "".join(out)
    if raw_value in front:
        return front.replace(raw_value, "https://example.com/hiring-contact", 1)
    return front


def _line_is_field(line: str, field: str, raw_value: str) -> bool:
    stripped = line.strip()
    prefix = field + ":"
    if not stripped.startswith(prefix):
        return False
    value = stripped[len(prefix) :].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value == raw_value


def _privacy_issues(text: str, rel: str) -> list[Issue]:
    issues: list[Issue] = []
    findings = find_contacts(text)
    extra = 0
    for finding in findings:
        if len(issues) >= 8:
            extra += 1
            continue
        if finding.kind == "email":
            code = "privacy-email"
            message = f"Line {finding.line} looks like an email address ({finding.detail})."
        elif finding.kind == "phone":
            code = "privacy-phone"
            message = f"Line {finding.line} looks like a phone number ({finding.detail})."
        else:
            code = "privacy-hidden"
            message = f"Line {finding.line} contains a hidden or direction-override character."
        issues.append(Issue(code, rel, message, FIX[code]))
    if extra:
        issues.append(
            Issue(
                "privacy-email",
                rel,
                f"{extra} more contact-detail matches were omitted from this report.",
                FIX["privacy-email"],
            )
        )
    return issues


def _schema_issues(meta: dict, rel: str) -> list[Issue]:
    kind = meta.get("kind")
    schemas = _validators()
    if kind not in schemas:
        allowed = ", ".join(sorted(schemas))
        return [
            Issue(
                "schema",
                rel,
                f"`kind` must be one of: {allowed}.",
                FIX["schema"],
            )
        ]
    issues: list[Issue] = []
    for error in sorted(schemas[kind].iter_errors(meta), key=_error_key):
        loc = "/".join(str(part) for part in error.absolute_path) or "front matter"
        fix = FIX["schema"]
        if error.validator == "additionalProperties":
            fix = (
                "Remove fields the schema does not define. There is no phone field. "
                "A hiring address belongs in `apply` or `apply_email` on a job, not in a field named `email`."
            )
        issues.append(Issue("schema", rel, f"{loc}: {error.message}", fix))
    return issues


def _error_key(error: ValidationError) -> list[object]:
    return list(error.absolute_path)


def _path_issues(rel: str, meta: dict) -> list[Issue]:
    kind = meta.get("kind")
    if kind == "job":
        match = JOB_PATH.fullmatch(rel)
        if match is None:
            return [_bad_path(rel, "jobs/YYYY/MM/<company>-<role-slug>.md")]
        issues: list[Issue] = []
        posted = meta.get("posted")
        if isinstance(posted, str) and DATE_RE.fullmatch(posted):
            if match.group(1) != posted[:4] or match.group(2) != posted[5:7]:
                issues.append(
                    _bad_path(
                        rel,
                        f"jobs/{posted[:4]}/{posted[5:7]}/<company>-<role-slug>.md to match `posted`",
                    )
                )
        company, role = meta.get("company"), meta.get("role_slug")
        if isinstance(company, str) and isinstance(role, str):
            expect = f"{company}-{role}"
            if match.group(3) != expect:
                issues.append(_bad_path(rel, f"jobs/{match.group(1)}/{match.group(2)}/{expect}.md"))
        return issues
    if kind in {"talent", "talent-ref"}:
        match = TALENT_PATH.fullmatch(rel)
        if match is None:
            return [_bad_path(rel, "talents/<first-letter>/<github-username>.md")]
        github = meta.get("github")
        if isinstance(github, str) and github:
            handle = github.lower()
            if match.group(2) != handle or match.group(1) != handle[0]:
                return [_bad_path(rel, f"talents/{handle[0]}/{handle}.md")]
        return []
    if kind == "company":
        match = COMPANY_PATH.fullmatch(rel)
        if match is None:
            return [_bad_path(rel, "companies/<first-letter>/<slug>.md")]
        slug = meta.get("slug")
        if isinstance(slug, str) and slug:
            if match.group(2) != slug or match.group(1) != slug[0]:
                return [_bad_path(rel, f"companies/{slug[0]}/{slug}.md")]
        return []
    root = rel.split("/", 1)[0]
    if root not in KIND_ROOT.values():
        return [_bad_path(rel, "jobs/, talents/, or companies/")]
    return []


def _bad_path(rel: str, expected: str) -> Issue:
    return Issue(
        "bad-path",
        rel,
        f"This path does not match the required layout. Expected `{expected}`.",
        FIX["bad-path"],
    )


def _body_issues(body: str, rel: str) -> list[Issue]:
    if len(body.strip()) < MIN_BODY_CHARS:
        return [
            Issue(
                "body",
                rel,
                f"The body is shorter than {MIN_BODY_CHARS} characters.",
                FIX["body"],
            )
        ]
    return []


def _link_issues(meta: dict, body: str, rel: str) -> list[Issue]:
    issues: list[Issue] = []
    if DANGEROUS_URL.search(body):
        issues.append(
            Issue(
                "spam-link",
                rel,
                "The body contains a `javascript:` or `data:` URL.",
                FIX["spam-link"],
            )
        )
    urls: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(meta)
    urls.extend(BODY_URL.findall(body))
    cleaned = [url.rstrip(".,);]}>\"'") for url in urls]
    if len(cleaned) > MAX_LINKS:
        issues.append(
            Issue(
                "spam-link",
                rel,
                f"The post has {len(cleaned)} links. The limit is {MAX_LINKS}.",
                FIX["spam-link"],
            )
        )
    seen: set[str] = set()
    for url in cleaned:
        if url in seen:
            continue
        seen.add(url)
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
            issues.append(
                Issue(
                    "spam-link",
                    rel,
                    "A link contains a username or password. Remove it.",
                    FIX["spam-link"],
                )
            )
            continue
        if _is_shortener(host):
            issues.append(
                Issue(
                    "spam-link",
                    rel,
                    f"`{host}` is a URL shortener. Paste the full `https://` destination.",
                    FIX["spam-link"],
                )
            )
    return issues


def _is_shortener(host: str) -> bool:
    return any(host == name or host.endswith("." + name) for name in SHORTENERS)


def _date_issues(
    meta: dict,
    *,
    today: date,
    new_file: bool,
    base_meta: dict | None,
    rel: str,
) -> list[Issue]:
    kind = meta.get("kind")
    if kind not in KIND_ROOT:
        return []
    issues: list[Issue] = []
    posted = _maybe_date(meta.get("posted"))
    if not isinstance(meta.get("posted"), str) or posted is None:
        if isinstance(meta.get("posted"), str):
            issues.append(Issue("dates", rel, "`posted` is not a real calendar date.", FIX["dates"]))
        return issues
    if base_meta is not None and base_meta.get("posted") != meta.get("posted"):
        issues.append(
            Issue(
                "posted-immutable",
                rel,
                f"`posted` was `{base_meta.get('posted')}` and cannot change.",
                FIX["posted-immutable"],
            )
        )
    renewed = None
    if meta.get("renewed"):
        renewed = _maybe_date(meta.get("renewed"))
        if renewed is None:
            issues.append(Issue("dates", rel, "`renewed` is not a real calendar date.", FIX["dates"]))
        elif renewed < posted:
            issues.append(Issue("dates", rel, "`renewed` is earlier than `posted`.", FIX["dates"]))
        elif renewed > today + timedelta(days=FUTURE_SKEW_DAYS):
            issues.append(Issue("dates", rel, "`renewed` is too far in the future.", FIX["dates"]))
    window_start = today - timedelta(days=NEW_POST_MAX_AGE_DAYS)
    future_limit = today + timedelta(days=FUTURE_SKEW_DAYS)
    fresh_required = new_file and meta.get("example") is not True
    renewed_changed = meta.get("renewed") and (
        base_meta is None or base_meta.get("renewed") != meta.get("renewed")
    )
    if fresh_required and (posted < window_start or posted > future_limit):
        issues.append(
            Issue(
                "dates",
                rel,
                f"`posted` must fall between {window_start.isoformat()} and {future_limit.isoformat()}.",
                FIX["dates"],
            )
        )
    if renewed_changed and renewed is not None and renewed < window_start:
        issues.append(
            Issue(
                "dates",
                rel,
                f"`renewed` must be on or after {window_start.isoformat()}.",
                FIX["dates"],
            )
        )
    if fresh_required:
        probe = dict(meta)
        probe["example"] = False
        expires_on = effective_expiry(probe)
        if expires_on is not None and expires_on < today:
            issues.append(
                Issue(
                    "expiry",
                    rel,
                    "This post is already expired. Set `renewed` to today or choose a later `expires` within the cap.",
                    FIX["expiry"],
                )
            )
    if meta.get("expires"):
        expires = _maybe_date(meta.get("expires"))
        if expires is None:
            issues.append(Issue("dates", rel, "`expires` is not a real calendar date.", FIX["dates"]))
        elif kind == "company":
            issues.append(Issue("expiry", rel, "Company pages do not take an `expires` field.", FIX["expiry"]))
        else:
            start = renewed or posted
            days = JOB_DAYS if kind == "job" else TALENT_DAYS
            cap = start + timedelta(days=days)
            if expires < posted:
                issues.append(Issue("expiry", rel, "`expires` is earlier than `posted`.", FIX["expiry"]))
            elif expires > cap:
                issues.append(
                    Issue(
                        "expiry",
                        rel,
                        f"`expires` is after {cap.isoformat()}. "
                        f"{'Jobs' if kind == 'job' else 'Talent posts'} stay up at most {days} days "
                        "from `posted`, or from `renewed` when that is set.",
                        FIX["expiry"],
                    )
                )
    return issues


def _federated_issues(meta: dict, rel: str) -> list[Issue]:
    if meta.get("kind") != "talent-ref":
        return []
    url = meta.get("profile_url")
    github = meta.get("github")
    if not isinstance(url, str) or not isinstance(github, str):
        return []
    match = PROFILE_URL.fullmatch(url)
    if match is None or match.group(1).lower() != github.lower():
        return [
            Issue(
                "federated-url",
                rel,
                "`profile_url` must point at the same person's `<github>/openjob-profile` repository.",
                FIX["federated-url"],
            )
        ]
    return []


def _ownership_issues(
    meta: dict,
    *,
    rel: str,
    author: str,
    base_meta: dict | None,
) -> list[Issue]:
    author_l = author.lower()
    owner = owner_of(meta)
    issues: list[Issue] = []
    if owner != author_l:
        issues.append(
            Issue(
                "ownership",
                rel,
                f"This post is tied to `{owner or 'nobody'}` but the pull request author is `{author}`.",
                FIX["ownership"],
            )
        )
    if base_meta is not None and owner_of(base_meta) != author_l:
        issues.append(
            Issue(
                "ownership",
                rel,
                f"The published post belongs to `{owner_of(base_meta)}`. "
                f"`{author}` cannot edit or replace it.",
                FIX["ownership"],
            )
        )
    return issues


def _example_issues(
    meta: dict,
    *,
    rel: str,
    author: str,
    maintainers: set[str],
    base_meta: dict | None,
) -> list[Issue]:
    if meta.get("example") is not True:
        return []
    if author.lower() in maintainers:
        return []
    if base_meta is not None and base_meta.get("example") is True and owner_of(base_meta) == author.lower():
        return []
    return [
        Issue(
            "example",
            rel,
            "`example: true` is only for sample posts committed by a maintainer.",
            FIX["example"],
        )
    ]


def _maybe_date(value: object) -> date | None:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _canon(value: object) -> object:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _canon(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canon(item) for item in value]
    return value


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


@lru_cache(maxsize=1)
def _validators() -> dict[str, Draft202012Validator]:
    schema_dir = Path(__file__).resolve().parent.parent / "schema"
    resources: list[tuple[str, Resource]] = []
    documents: dict[str, dict] = {}
    for path in sorted(schema_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        documents[path.name] = document
        resources.append((document["$id"], Resource.from_contents(document)))
    registry = Registry().with_resources(resources)
    names = {
        "job": "job.schema.json",
        "talent": "talent.schema.json",
        "talent-ref": "talent-ref.schema.json",
        "company": "company.schema.json",
    }
    return {
        kind: Draft202012Validator(documents[filename], registry=registry)
        for kind, filename in names.items()
    }


def index_validator() -> Draft202012Validator:
    schema_dir = Path(__file__).resolve().parent.parent / "schema"
    document = json.loads((schema_dir / "index.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(document)
