"""Detect emails and phone numbers, including common obfuscations.

Allow-list, on purpose narrow:

- Email domains ``example.com``, ``example.org``, ``example.net``, and ``example.edu``
  (and their subdomains). These are documentation domains, not inboxes.
- NANP numbers reserved for fiction: exchange ``555`` and line ``01xx``
  (for example ``415-555-0100``), and only when the text is formatted as a phone
  number rather than a bare digit run.

Chinese mobiles such as ``13800138000`` are rejected. That number is widely copied
as a placeholder and is indistinguishable from a real mobile.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote

ALLOW_EMAIL_DOMAINS = frozenset(
    {"example.com", "example.org", "example.net", "example.edu"}
)

MAIL_HOSTS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "yahoo.com",
        "icloud.com",
        "me.com",
        "proton.me",
        "protonmail.com",
        "qq.com",
        "163.com",
        "126.com",
        "sina.com",
        "sina.cn",
        "foxmail.com",
        "yeah.net",
        "pm.me",
        "tutanota.com",
        "fastmail.com",
        "mail.com",
        "gmx.com",
        "yandex.com",
        "zoho.com",
    }
)

ZH_DIGITS = str.maketrans(
    {
        "零": "0",
        "〇": "0",
        "○": "0",
        "一": "1",
        "壹": "1",
        "二": "2",
        "贰": "2",
        "貳": "2",
        "两": "2",
        "兩": "2",
        "三": "3",
        "叁": "3",
        "參": "3",
        "四": "4",
        "肆": "4",
        "五": "5",
        "伍": "5",
        "六": "6",
        "陆": "6",
        "陸": "6",
        "七": "7",
        "柒": "7",
        "八": "8",
        "捌": "8",
        "九": "9",
        "玖": "9",
    }
)

HIDDEN_CHARS = re.compile(r"[\u200b\u200c\u200d\ufeff\u2060\u180e\u202a-\u202e\u2066-\u2069]")
SEPS = r"[\s.\-·•,，]"

STANDARD_EMAIL = re.compile(
    r"(?<![\w.+-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})"
    r"@"
    r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?)+)"
)
BRACKET_EMAIL = re.compile(
    r"(?ix)(?<![\w.+-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})"
    r"\s*(?:\[at\]|\(at\)|\{at\}|<at>)\s*"
    r"([A-Za-z0-9-]+(?:\s*(?:\[dot\]|\(dot\)|\{dot\}|<dot>|\.)\s*[A-Za-z0-9-]+)+)"
)
WORD_DOT_EMAIL = re.compile(
    r"(?ix)(?<![\w.+-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})"
    r"\s+at\s+"
    r"([A-Za-z0-9-]+(?:\s*(?:\[dot\]|\(dot\)|\{dot\}|<dot>|dot)\s*[A-Za-z0-9-]+)+)"
)
WORD_HOST_EMAIL = re.compile(
    r"(?ix)(?<![\w.+-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})"
    r"\s+at\s+"
    r"((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})"
)
MAILTO = re.compile(r"(?i)\bmailto\s*:")
TEL = re.compile(r"(?i)\btel\s*:")

CN_MOBILE = re.compile(
    rf"(?<!\d)(?:(?:\+|00)86{SEPS}?)?(1[3-9]\d(?:{SEPS}?\d){{8}})(?!\d)"
)
CN_LANDLINE = re.compile(
    rf"(?<!\d)(?:(?:\+|00)86{SEPS}?)?0\d{{2,3}}{SEPS}\d{{7,8}}(?!\d)"
)
CN_SERVICE = re.compile(rf"(?<!\d)(?:400|800)(?:{SEPS}?\d){{7}}(?!\d)")
INTL = re.compile(rf"(?<!\d)\+\d{{1,3}}(?:{SEPS}?\d){{7,14}}(?!\d)")
NANP = re.compile(
    rf"(?<!\d)(?:\+1{SEPS}?)?\(?([2-9]\d{{2}})\)?{SEPS}([2-9]\d{{2}}){SEPS}(\d{{4}})(?!\d)"
)


@dataclass(frozen=True)
class Finding:
    kind: str
    line: int
    detail: str


def find_contacts(text: str) -> list[Finding]:
    """Return redacted email, phone, and hidden-character findings."""
    findings: list[Finding] = []
    for match in HIDDEN_CHARS.finditer(text):
        findings.append(Finding("hidden", _line_at(text, match.start()), "hidden character"))
        break

    prepared = _prepare(text)
    spans: list[tuple[int, int, str, str]] = []
    for regex in (STANDARD_EMAIL, BRACKET_EMAIL, WORD_DOT_EMAIL):
        for match in regex.finditer(prepared):
            spans.append((match.start(), match.end(), "email", match.group(0)))
    for match in WORD_HOST_EMAIL.finditer(prepared):
        domain = match.group(2).lower().strip(".")
        if domain in MAIL_HOSTS:
            spans.append((match.start(), match.end(), "email", match.group(0)))
    if MAILTO.search(prepared):
        match = MAILTO.search(prepared)
        assert match is not None
        spans.append((match.start(), match.end(), "email", match.group(0)))

    phone_text = prepared.translate(ZH_DIGITS)
    for regex, checker in (
        (CN_MOBILE, _cn_mobile_ok),
        (CN_LANDLINE, _digits_between(10, 15)),
        (CN_SERVICE, _digits_between(10, 11)),
        (INTL, _digits_between(8, 15)),
        (NANP, _nanp_ok),
    ):
        for match in regex.finditer(phone_text):
            if checker(match.group(0)):
                spans.append((match.start(), match.end(), "phone", match.group(0)))
    if TEL.search(phone_text):
        match = TEL.search(phone_text)
        assert match is not None
        spans.append((match.start(), match.end(), "phone", match.group(0)))

    spans.sort(key=lambda item: (item[0], item[1]))
    last_end = -1
    for start, end, kind, raw in spans:
        if start < last_end:
            continue
        last_end = end
        if kind == "email" and _email_allowed(raw):
            continue
        if kind == "phone" and _phone_allowed(raw):
            continue
        detail = _redact_email(raw) if kind == "email" else _redact_phone(raw)
        findings.append(Finding(kind, _line_at(prepared, start), detail))
    return findings


def _prepare(text: str) -> str:
    cleaned = HIDDEN_CHARS.sub("", text)
    cleaned = html.unescape(cleaned)
    cleaned = unquote(unquote(cleaned))
    return unicodedata.normalize("NFKC", cleaned)


def _line_at(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _cn_mobile_ok(raw: str) -> bool:
    digits = _digits(raw)
    if digits.startswith("0086"):
        digits = digits[4:]
    elif digits.startswith("86") and len(digits) > 11:
        digits = digits[2:]
    return len(digits) == 11 and digits[0] == "1" and digits[1] in "3456789"


def _digits_between(low: int, high: int):
    def check(raw: str) -> bool:
        count = len(_digits(raw))
        return low <= count <= high

    return check


def _nanp_ok(raw: str) -> bool:
    digits = _digits(raw)
    if digits.startswith("1") and len(digits) == 11:
        national = digits[1:]
    elif len(digits) == 10:
        national = digits
    else:
        return False
    npa, nxx = national[:3], national[3:6]
    return npa[0] not in "01" and nxx[0] not in "01"


def _unwrap_domain(raw: str) -> str:
    domain = re.sub(r"(?i)\s*(?:\[dot\]|\(dot\)|\{dot\}|<dot>|dot)\s*", ".", raw)
    return re.sub(r"\s+", "", domain).strip(".").lower()


def _email_allowed(raw: str) -> bool:
    normalized = unicodedata.normalize("NFKC", raw)
    if "@" not in normalized:
        normalized = re.sub(
            r"(?i)\s*(?:\[at\]|\(at\)|\{at\}|<at>|\bat\b)\s*",
            "@",
            normalized,
            count=1,
        )
    if "@" not in normalized:
        return False
    local, _, domain = normalized.partition("@")
    if not local.strip():
        return False
    domain = _unwrap_domain(domain)
    return any(domain == allowed or domain.endswith("." + allowed) for allowed in ALLOW_EMAIL_DOMAINS)


def _phone_allowed(raw: str) -> bool:
    """Allow only formatted fictional NANP 555-01xx numbers."""
    if not re.search(r"[+()]", raw) and not re.search(r"\d[\s.\-]\d", raw):
        return False
    digits = _digits(raw)
    if len(digits) == 11 and digits.startswith("1"):
        national = digits[1:]
    elif len(digits) == 10:
        national = digits
    else:
        return False
    nxx, line = national[3:6], national[6:]
    return nxx == "555" and line.startswith("01")


def _redact_email(raw: str) -> str:
    compact = re.sub(r"\s+", "", raw)
    if "@" in compact:
        local, _, domain = compact.partition("@")
        return f"{local[:1]}***@{domain}"
    return "*** (obfuscated email)"


def _redact_phone(raw: str) -> str:
    digits = _digits(raw)
    if len(digits) < 5:
        return "a phone number"
    return f"{digits[:3]}****{digits[-2:]}"
