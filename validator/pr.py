"""Compare a pull request head with its base and decide whether it can auto-merge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from validator.issues import FIX, Issue, render_report
from validator.posts import (
    PostParseError,
    author_owns,
    foreign_post_issues,
    is_expired,
    is_post_path,
    is_post_tree,
    load_post,
    maintainers_from,
    ownership_issues,
    validate_post,
)
from validator.share import render_share_comment

BOT = "github-actions[bot]"


@dataclass(frozen=True)
class Result:
    issues: list[Issue]
    notes: list[str]
    automerge: bool
    share_comment: str | None = None

    def report(self) -> str:
        return render_report(title_failed=bool(self.issues), issues=self.issues, notes=self.notes)


def check_pr(*, head: Path, base: Path, author: str, today: date | None = None) -> Result:
    today = today or datetime.now(timezone.utc).date()
    if not head.is_dir():
        return Result(
            issues=[
                Issue(
                    "checkout",
                    ".",
                    "The pull request files are not on disk, so this run did not judge any post.",
                    FIX["checkout"],
                )
            ],
            notes=[],
            automerge=False,
        )
    maintainers = maintainers_from(base)
    head_files = _files(head)
    base_files = _files(base)
    added, modified, deleted = _changes(head_files, base_files)

    issues: list[Issue] = []
    for rel in added + modified:
        path = head_files[rel]
        if path.is_symlink():
            issues.append(Issue("symlink", rel, "Symlinks are not allowed.", FIX["symlink"]))
            continue
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 1_000_000:
            issues.append(
                Issue(
                    "oversize",
                    rel,
                    f"`{rel}` is {path.stat().st_size} bytes. Files over 1 MB are rejected.",
                    FIX["oversize"],
                )
            )

    post_added = [rel for rel in added if is_post_path(rel)]
    post_modified = [rel for rel in modified if is_post_path(rel)]
    post_deleted = [rel for rel in deleted if is_post_path(rel)]
    stray = [
        rel
        for rel in added + modified + deleted
        if is_post_tree(rel) and not is_post_path(rel)
    ]
    for rel in stray:
        path = head_files.get(rel)
        if path is not None and path.is_file() and not path.is_symlink():
            issues.extend(foreign_post_issues(path, rel))
        elif rel in base_files:
            issues.extend(foreign_post_issues(base_files[rel], rel))

    other = [rel for rel in added + modified + deleted if not is_post_tree(rel)]

    bot_expiry = _bot_expiry(
        author=author,
        other=other,
        post_added=post_added,
        post_modified=post_modified,
        post_deleted=post_deleted,
        base_files=base_files,
        today=today,
        issues=issues,
    )

    if not bot_expiry:
        for rel in post_added:
            issues.extend(
                validate_post(
                    root=head,
                    rel=rel,
                    today=today,
                    author=author,
                    maintainers=maintainers,
                    base_root=base,
                    new_file=True,
                )
            )
        for rel in post_modified:
            base_meta = _meta(base_files.get(rel))
            issues.extend(
                validate_post(
                    root=head,
                    rel=rel,
                    today=today,
                    author=author,
                    maintainers=maintainers,
                    base_meta=base_meta,
                    base_root=base,
                    new_file=False,
                )
            )
        for rel in post_deleted:
            base_meta = _meta(base_files.get(rel))
            if base_meta is None:
                issues.append(
                    Issue(
                        "ownership",
                        rel,
                        "The deleted post could not be read, so ownership could not be checked.",
                        FIX["ownership"],
                    )
                )
                continue
            issues.extend(
                ownership_issues(
                    base_meta,
                    rel=rel,
                    author=author,
                    base_meta=base_meta,
                    head=base,
                    base=base,
                    new_file=False,
                    maintainers=maintainers,
                    deleting=True,
                )
            )
        if len(post_added) > 1:
            listed = ", ".join(f"`{rel}`" for rel in post_added)
            issues.append(
                Issue(
                    "one-post",
                    "(pull request)",
                    f"This pull request adds {len(post_added)} new posts ({listed}). "
                    "Add one new post per pull request.",
                    FIX["one-post"],
                )
            )
        issues.extend(_duplicate_issues(head, post_added))

    post_changes = post_added + post_modified + post_deleted
    scope_issue: Issue | None = None
    bot_ready = bot_expiry and not issues
    # Any path outside the post trees needs a team review. Several post files are allowed.
    maintainer_pr = bool(other) and not bot_ready
    if bot_ready or maintainer_pr:
        pass
    elif not post_changes:
        scope_issue = Issue(
            "scope",
            "(pull request)",
            "The pull request does not add, edit, or remove a post.",
            FIX["scope"],
        )

    # Re-check the whole head tree so a maintainer pull request cannot land a post the checker rejects.
    if not bot_expiry:
        from validator.posts import validate_tree

        known = {(issue.code, issue.path, issue.message) for issue in issues}
        for issue in validate_tree(head, today=today):
            key = (issue.code, issue.path, issue.message)
            if key in known or issue.code == "ownership":
                continue
            issues.append(issue)
            known.add(key)

    if scope_issue is not None:
        issues.append(scope_issue)
    notes: list[str] = []
    automerge = False
    share_comment: str | None = None
    new_companies = _new_companies(post_added, head_files)
    owns_every_file = bot_expiry or _author_owns_every(
        author=author,
        head=head,
        base=base,
        head_files=head_files,
        base_files=base_files,
        post_added=post_added,
        post_modified=post_modified,
        post_deleted=post_deleted,
    )
    if not issues and bot_ready:
        automerge = True
        notes.append(
            "This is the expiry workflow removing posts that are already past their expiry date. "
            "It can be squash-merged."
        )
    elif maintainer_pr:
        outside = ", ".join(f"`{rel}`" for rel in other)
        notes.append(
            "This pull request changes files outside `jobs/`, `talents/`, and `companies/` "
            f"({outside}). Auto-merge stays off. It needs approval from the Softprobe team "
            "(`@softprobe/openjob-maintainers`)."
        )
    elif not issues and new_companies:
        notes.append(
            "A new company page is reviewed once by `@softprobe/openjob-maintainers`. "
            "Auto-merge stays off. After it is on the board, the people in `owners` can edit "
            "the page and its jobs, and those pull requests can auto-merge."
        )
    elif not issues and not owns_every_file:
        notes.append(
            f"`{author}` does not own every file in this pull request. Auto-merge stays off. "
            "A maintainer (`@softprobe/openjob-maintainers`) can merge it after review."
        )
    elif not issues:
        automerge = True
        share_comment = _share_comments(post_added, post_modified, head_files)
        note = (
            "Checks passed. Every changed file is a post under `jobs/`, `talents/`, or `companies/`. "
            "The author owns each one. It can be squash-merged with the GitHub Actions token."
        )
        if share_comment:
            note += " The merge comment includes the permalink and the share links."
        notes.append(note)
    return Result(issues=issues, notes=notes, automerge=automerge, share_comment=share_comment)


def _new_companies(added: list[str], head_files: dict[str, Path]) -> list[str]:
    found: list[str] = []
    for rel in added:
        meta = _meta(head_files.get(rel))
        if meta is not None and meta.get("kind") == "company":
            found.append(rel)
    return found


def _author_owns_every(
    *,
    author: str,
    head: Path,
    base: Path,
    head_files: dict[str, Path],
    base_files: dict[str, Path],
    post_added: list[str],
    post_modified: list[str],
    post_deleted: list[str],
) -> bool:
    for rel in post_added:
        meta = _meta(head_files.get(rel))
        if meta is None or not author_owns(
            meta,
            rel=rel,
            author=author,
            base_meta=None,
            head=head,
            base=base,
            new_file=True,
        ):
            return False
    for rel in post_modified:
        meta = _meta(head_files.get(rel))
        base_meta = _meta(base_files.get(rel))
        if meta is None or not author_owns(
            meta,
            rel=rel,
            author=author,
            base_meta=base_meta,
            head=head,
            base=base,
            new_file=False,
        ):
            return False
    for rel in post_deleted:
        base_meta = _meta(base_files.get(rel))
        if base_meta is None or not author_owns(
            base_meta,
            rel=rel,
            author=author,
            base_meta=base_meta,
            head=base,
            base=base,
            new_file=False,
            deleting=True,
        ):
            return False
    return True


def _bot_expiry(
    *,
    author: str,
    other: list[str],
    post_added: list[str],
    post_modified: list[str],
    post_deleted: list[str],
    base_files: dict[str, Path],
    today: date,
    issues: list[Issue],
) -> bool:
    if author.lower() != BOT:
        return False
    if other or post_added or post_modified or not post_deleted:
        return False
    allowed = True
    for rel in post_deleted:
        meta = _meta(base_files.get(rel))
        if meta is None or not is_expired(meta, today):
            allowed = False
            issues.append(
                Issue(
                    "bot-expiry",
                    rel,
                    "The expiry workflow tried to delete a post that is still live.",
                    FIX["bot-expiry"],
                )
            )
    return allowed and not any(issue.code == "bot-expiry" for issue in issues)


def _duplicate_issues(head: Path, added: list[str]) -> list[Issue]:
    """Flag a new job that repeats a company and title, or a new talent login."""
    from validator.posts import PostParseError, iter_post_files, load_post

    metas: dict[str, dict] = {}
    for rel, path in iter_post_files(head):
        try:
            meta, _body = load_post(path)
        except (OSError, PostParseError, UnicodeError):
            continue
        metas[rel] = meta
    issues: list[Issue] = []
    for rel in added:
        meta = metas.get(rel)
        if meta is None:
            continue
        kind = meta.get("kind")
        if kind == "job":
            company = str(meta.get("company") or "").casefold()
            title = str(meta.get("title") or "").strip().casefold()
            if not company or not title:
                continue
            for other, other_meta in metas.items():
                if other == rel or other_meta.get("kind") != "job":
                    continue
                same_company = str(other_meta.get("company") or "").casefold() == company
                same_title = str(other_meta.get("title") or "").strip().casefold() == title
                if same_company and same_title:
                    issues.append(
                        Issue(
                            "duplicate",
                            rel,
                            f"{rel}: company `{meta.get('company')}` and title `{meta.get('title')}` "
                            f"already exist at `{other}`. Edit that file instead of adding another.",
                            FIX["duplicate"],
                        )
                    )
                    break
        elif kind in {"talent", "talent-ref"}:
            handle = str(meta.get("github") or "").casefold()
            if not handle:
                continue
            for other, other_meta in metas.items():
                if other == rel or other_meta.get("kind") not in {"talent", "talent-ref"}:
                    continue
                if str(other_meta.get("github") or "").casefold() == handle:
                    issues.append(
                        Issue(
                            "duplicate",
                            rel,
                            f"{rel}: GitHub login `{meta.get('github')}` already has `{other}`. "
                            "Edit that file instead of adding another.",
                            FIX["duplicate"],
                        )
                    )
                    break
    return issues


def _share_comments(
    added: list[str], modified: list[str], head_files: dict[str, Path]
) -> str | None:
    """Share every post this pull request adds or edits. A pure deletion has nothing to share."""
    parts: list[str] = []
    for rel in added + modified:
        meta = _meta(head_files.get(rel))
        if meta is not None:
            parts.append(render_share_comment(meta, rel))
    if not parts:
        return None
    return "\n".join(parts)


def _meta(path: Path | None) -> dict | None:
    if path is None or not path.is_file() or path.is_symlink():
        return None
    try:
        meta, _body = load_post(path)
    except (OSError, PostParseError, UnicodeError):
        return None
    return meta


def _files(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or "/__pycache__/" in f"/{rel}" or rel.endswith(".pyc"):
            continue
        found[rel] = path
    return found


def _changes(
    head_files: dict[str, Path], base_files: dict[str, Path]
) -> tuple[list[str], list[str], list[str]]:
    added: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    for rel in sorted(set(head_files) | set(base_files)):
        in_head = rel in head_files
        in_base = rel in base_files
        if in_head and not in_base:
            added.append(rel)
        elif in_base and not in_head:
            deleted.append(rel)
        elif _bytes(head_files[rel]) != _bytes(base_files[rel]):
            modified.append(rel)
    return added, modified, deleted


def _bytes(path: Path) -> bytes:
    if path.is_symlink():
        return b"symlink:" + str(path.readlink()).encode()
    return path.read_bytes()
