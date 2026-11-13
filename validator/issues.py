"""Validation issues and the pull-request report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str
    fix: str

    def format_block(self) -> str:
        return f"### `{self.code}` — `{self.path}`\n\n{self.message}\n\n**How to fix:** {self.fix}"


FIX = {
    "privacy-email": (
        "Delete the address. Contact belongs in a LinkedIn URL, a GitHub profile, "
        "a personal site, or a company careers/apply link. The check looks through "
        "`name [at] domain [dot] com`, fullwidth characters, HTML entities, and "
        "`%40` encoding."
    ),
    "privacy-phone": (
        "Delete the number, including `+86` mobiles, numbers split by spaces or dashes, "
        "Chinese numerals (一三八…), and `tel:` links. Use a profile or careers link instead."
    ),
    "privacy-hidden": (
        "Remove zero-width and bidirectional override characters. They are treated as "
        "an attempt to hide an address or a number."
    ),
    "schema": "Match the template and the JSON Schema for this kind of post. Field names are exact.",
    "bad-path": (
        "Move the file to the sharded path for its kind: "
        "`jobs/YYYY/MM/<company>-<role-slug>.md`, "
        "`talents/<first-letter>/<github-username>.md`, or "
        "`companies/<first-letter>/<slug>.md`. Use lowercase. `YYYY/MM` is the `posted` month."
    ),
    "oversize": f"Shorten the file to {10 * 1024} bytes or fewer. Posts are text only.",
    "binary": "Remove the file. Images, PDFs, archives, and other binaries are not accepted.",
    "encoding": "Save the file as UTF-8 without a binary payload.",
    "symlink": "Replace the symlink with a normal Markdown file.",
    "front-matter": "Start the file with `---` YAML front matter and close it with a `---` line.",
    "body": "Write at least a short plain-language description (40 characters or more).",
    "spam-link": (
        "Use a normal `https://` link. URL shorteners (`bit.ly`, `t.co`, `t.cn`, and similar), "
        "`javascript:` URLs, and links with a username or password are rejected."
    ),
    "ownership": (
        "The GitHub login on the post (`github` for a talent, `posted_by` for a job or company) "
        "must be the pull request author. Only that account can edit or delete the file."
    ),
    "posted-immutable": "Keep the original `posted` date. Set `renewed` to the day you renew.",
    "dates": "Use real `YYYY-MM-DD` dates. A new post's `posted` date has to be recent.",
    "expiry": "Jobs last at most 60 days and talent posts 180 days from `posted` or `renewed`.",
    "example": "Only a maintainer can set `example: true`, and only on a post they own.",
    "federated-url": (
        "Point `profile_url` at `https://github.com/<your-username>/openjob-profile` "
        "(or the raw file in that repo). The GitHub login in the URL has to match `github`."
    ),
    "scope": (
        "Submit exactly one post per pull request: one added, edited, or deleted file under "
        "`jobs/`, `talents/`, or `companies/`. A rename is one delete plus one add of the same kind. "
        "Open a separate pull request for each additional post."
    ),
    "bot-expiry": "The expiry workflow may only delete posts whose effective expiry is before today.",
}


def render_report(*, title_failed: bool, issues: list[Issue], notes: list[str]) -> str:
    lines: list[str] = []
    if issues and title_failed:
        lines.append("## OpenJob could not accept this pull request")
        lines.append("")
        lines.append(
            "Nothing was merged. Fix every item, push to this branch, and the check will run again. "
            "Contact details do not belong in the repo: use a LinkedIn URL, GitHub profile, personal site, "
            "or a company careers/apply link."
        )
        lines.append("")
        for issue in issues:
            lines.append(issue.format_block())
            lines.append("")
    else:
        lines.append("## OpenJob checks passed")
        lines.append("")
    for note in notes:
        lines.append(note)
        lines.append("")
    if not issues:
        lines.append(
            "Auto-merge (squash) runs only when the pull request touches exactly one post file "
            "and every check passed. A pull request that edits workflows, the site, or docs waits for a maintainer."
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
