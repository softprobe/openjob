"""One-line JSON Schema failures for the pull-request comment."""

from __future__ import annotations

import re

from jsonschema import ValidationError

from validator.share import pages_origin

PUBLIC_SCHEMA = {
    "job": "job.json",
    "talent": "talent.json",
    "company": "company.json",
    "talent-ref": "talent-ref.json",
}

# A value an author can paste, and the shape the schema allows.
# The strings come from schema/*.schema.json and schema/common.json.
_ADD = {
    "kind": ("job", "one of job, talent, talent-ref, company"),
    "title": ("Site reliability engineer", "a string of 4 to 120 characters"),
    "company": ("northwind", "a lowercase slug"),
    "company_name": ("Northwind", "a string of 1 to 80 characters"),
    "role_slug": ("site-reliability-engineer", "a lowercase slug"),
    "location": ("Remote", "a string of 1 to 80 characters"),
    "remote": ("true", "true, false, hybrid, remote, or onsite"),
    "languages": ("[en]", "a list of en, zh, ja, ko, es, fr, de, pt, ru"),
    "tags": ("[reliability]", "up to 8 lowercase slugs"),
    "apply": ("https://example.com/jobs/role", "an https URL, or one mailto: on the company domain"),
    "posted": ("2026-11-14", "YYYY-MM-DD, within the last 45 days"),
    "posted_by": ("ada", "the pull request author's GitHub login"),
    "owners": ("[ada]", "a list of GitHub logins, including yours"),
    "name": ("Ada Lovelace", "a string of 1 to 80 characters"),
    "github": ("ada", "the pull request author's GitHub login"),
    "headline": ("Site reliability engineer", "a string of 4 to 140 characters"),
    "open_to": ("[contract]", "full-time, part-time, contract, or internship"),
    "slug": ("northwind", "a lowercase slug"),
    "website": ("https://example.com", "an https URL"),
    "profile_url": (
        "https://github.com/ada/openjob-profile",
        "https://github.com/<login>/openjob-profile",
    ),
}

_REQUIRED = re.compile(r"^'([^']+)' is a required property$")
_UNEXPECTED = re.compile(r"\('([^']+)' was unexpected\)")


def schema_public_url(kind: str | None) -> str:
    name = PUBLIC_SCHEMA.get(kind or "", "job.json")
    return f"{pages_origin().rstrip('/')}/schema/{name}"


def schema_failure(rel: str, kind: object, error: ValidationError) -> tuple[str, str]:
    """Return ``(message, fix)`` for one schema error."""
    field = _field(error)
    sentence, fix = _sentence(error, field)
    url = schema_public_url(kind if isinstance(kind, str) else None)
    if field:
        message = f"{rel}: field `{field}` {sentence}"
    else:
        message = f"{rel}: {sentence}"
    return message, f"{fix} See {url}."


def _field(error: ValidationError) -> str:
    if error.validator == "required":
        match = _REQUIRED.match(error.message)
        if match:
            return match.group(1)
    if error.validator == "additionalProperties":
        match = _UNEXPECTED.search(error.message)
        if match:
            return match.group(1)
    return "/".join(str(part) for part in error.absolute_path)


def _sentence(error: ValidationError, field: str) -> tuple[str, str]:
    validator = error.validator
    if validator == "required":
        add, shape = _ADD.get(field, (field or "value", "the type in the schema"))
        return "is missing.", f"Add `{field}: {add}` ({shape})."
    if validator == "additionalProperties":
        return (
            "is not a field on this post.",
            f"Remove `{field}`.",
        )
    if validator in {"enum", "const"}:
        allowed = error.validator_value
        if isinstance(allowed, list):
            shown = ", ".join(str(item) for item in allowed)
        else:
            shown = str(allowed)
        return f"is not allowed ({error.instance!r}).", f"Use one of: {shown}."
    if validator == "type":
        return (
            f"is {error.instance!r}, which is not a {error.validator_value}.",
            f"Set `{field}` to a {error.validator_value}.",
        )
    if validator == "minLength":
        return (
            f"is shorter than {error.validator_value} characters.",
            f"Write at least {error.validator_value} characters.",
        )
    if validator == "maxLength":
        return (
            f"is longer than {error.validator_value} characters.",
            f"Shorten it to {error.validator_value} characters or fewer.",
        )
    if validator == "pattern":
        return (
            f"does not match `{error.validator_value}`.",
            "Use the pattern from the schema.",
        )
    if validator == "format":
        return f"is not a {error.validator_value}.", f"Use a {error.validator_value}."
    if validator == "minItems":
        return (
            f"needs at least {error.validator_value} item.",
            f"Add at least {error.validator_value} item.",
        )
    if validator == "maxItems":
        return (
            f"has more than {error.validator_value} items.",
            f"Keep at most {error.validator_value} items.",
        )
    if validator == "uniqueItems":
        return "repeats a value.", "Remove the duplicate."
    if validator in {"minimum", "exclusiveMinimum"}:
        return f"is below the minimum ({error.validator_value}).", "Use a larger number."
    if validator in {"maximum", "exclusiveMaximum"}:
        return f"is above the maximum ({error.validator_value}).", "Use a smaller number."
    if validator == "oneOf":
        return "does not match an allowed shape.", "Use one of the shapes in the schema."
    return error.message.rstrip(".") + ".", "Match the schema."
