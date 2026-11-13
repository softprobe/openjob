"""Fail-closed decision for auto-merge.

The workflow looks up the ``validate`` check on the pull request head SHA and
passes that conclusion and SHA here. A post is merged only when the trusted
checker accepted the pull request and Validate succeeded for that same commit.
Any other state stays open.
"""

from __future__ import annotations

MARKER = "<!-- openjob-merge-gate -->"


def merge_allowed(
    *,
    automerge: bool,
    validate_conclusion: str | None,
    validate_sha: str | None,
    head_sha: str | None,
) -> bool:
    conclusion = (validate_conclusion or "").strip()
    return bool(
        automerge
        and head_sha
        and validate_sha
        and validate_sha == head_sha
        and conclusion == "success"
    )


def refusal_comment(
    *,
    head_sha: str | None,
    validate_conclusion: str | None,
    validate_sha: str | None = None,
) -> str:
    sha = head_sha or "unknown"
    conclusion = (validate_conclusion or "").strip()
    if validate_sha and head_sha and validate_sha != head_sha:
        reason = (
            f"Validate reported `{validate_sha}`, which is a different commit from the "
            f"pull request head `{sha}`."
        )
    elif not conclusion:
        reason = f"The `validate` check on `{sha}` did not finish."
    else:
        reason = f"The `validate` check on `{sha}` finished as `{conclusion}`."
    return (
        f"{MARKER}\n"
        "Auto-merge left this pull request open.\n\n"
        f"{reason} "
        "A post is squash-merged only when the trusted checker accepts it and "
        "the `validate` check succeeds for that same commit. "
        "The Validate comment on this pull request has the specific fix. "
        "Push an update and both checks run again. "
        "When they pass, the post merges on its own. "
        "Workflow, code, and documentation changes stay for a maintainer.\n"
    )
