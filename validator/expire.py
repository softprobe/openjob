"""Select posts whose effective expiry is before a given day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from validator.posts import effective_expiry, is_expired, iter_post_files, load_post


@dataclass(frozen=True)
class Expired:
    path: str
    kind: str
    title: str
    expires: date

    def format_line(self) -> str:
        return f"- `{self.path}` ({self.kind}, last day {self.expires.isoformat()}, {self.title})"


def select_expired(root: Path, *, today: date | None = None) -> list[Expired]:
    today = today or datetime.now(timezone.utc).date()
    found: list[Expired] = []
    for rel, path in iter_post_files(root):
        if not rel.endswith(".md") or path.is_symlink():
            continue
        try:
            meta, _body = load_post(path)
        except (OSError, UnicodeError, ValueError):
            continue
        if not is_expired(meta, today):
            continue
        expires = effective_expiry(meta)
        if expires is None:
            continue
        title = str(meta.get("title") or meta.get("name") or rel)
        found.append(Expired(path=rel, kind=str(meta.get("kind")), title=title, expires=expires))
    found.sort(key=lambda item: item.path)
    return found


def apply_removals(root: Path, expired: list[Expired]) -> None:
    for item in expired:
        path = root / item.path
        if path.is_file() and not path.is_symlink():
            path.unlink()
        parent = path.parent
        while parent != root and parent.exists() and parent.is_dir():
            if any(parent.iterdir()):
                break
            if parent.parent == root and parent.name in {"jobs", "talents", "companies"}:
                break
            parent.rmdir()
            parent = parent.parent


def render_expiry_report(expired: list[Expired], *, today: date) -> str:
    lines = [
        f"## Remove posts expired as of {today.isoformat()}",
        "",
        "Git history is the archive. These files are deleted from the live tree so the repository stays small.",
        "Each post remains in the history of this pull request. To put one back, restore the file from the parent commit, set `renewed` to the new day, and open a pull request.",
        "",
        "Sample posts (`example: true`) and company pages are not removed.",
        "",
    ]
    if not expired:
        lines.append("No posts were due for removal.")
    else:
        lines.append("### Removed")
        lines.append("")
        lines.extend(item.format_line() for item in expired)
    lines.append("")
    return "\n".join(lines)
