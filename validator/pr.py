"""Compare a pull request head with its base and decide whether it can auto-merge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from validator.issues import FIX, Issue, render_report
from validator.posts import (
    PostParseError,
    binary_issues,
    exempt_binary,
    is_expired,
    is_post_path,
    is_post_tree,
    load_post,
    maintainers_from,
    owner_of,
    validate_post,
)

BOT = "github-actions[bot]"


@dataclass(frozen=True)
class Result:
    issues: list[Issue]
    notes: list[str]
    automerge: bool

    def report(self) -> str:
        return render_report(title_failed=bool(self.issues), issues=self.issues, notes=self.notes)


def check_pr(*, head: Path, base: Path, author: str, today: date | None = None) -> Result:
    today = today or datetime.now(timezone.utc).date()
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
        if not exempt_binary(rel):
            issues.extend(binary_issues(path, rel))

    post_added = [rel for rel in added if is_post_path(rel)]
    post_modified = [rel for rel in modified if is_post_path(rel)]
    post_deleted = [rel for rel in deleted if is_post_path(rel)]
    stray = [rel for rel in added + modified + deleted if is_post_tree(rel) and not is_post_path(rel)]
    for rel in stray:
        issues.append(
            Issue(
                "bad-path",
                rel,
                "Only `.md` posts belong under jobs/, talents/, and companies/.",
                FIX["bad-path"],
            )
        )

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
            if owner_of(base_meta) != author.lower():
                issues.append(
                    Issue(
                        "ownership",
                        rel,
                        f"The deleted post belongs to `{owner_of(base_meta)}`. "
                        f"`{author}` cannot remove it.",
                        FIX["ownership"],
                    )
                )

    post_changes = post_added + post_modified + post_deleted
    single = _single_submission(post_added, post_modified, post_deleted, head, base_files)
    scope_issue: Issue | None = None
    maintainer_pr = False
    bot_ready = bot_expiry and not issues
    if bot_ready:
        pass
    elif other:
        maintainer_pr = True
    elif not post_changes:
        scope_issue = Issue(
            "scope",
            "(pull request)",
            "The pull request does not add, edit, or remove a post.",
            FIX["scope"],
        )
    elif not single:
        scope_issue = Issue(
            "scope",
            "(pull request)",
            "The pull request touches more than one post: "
            + ", ".join(f"`{rel}`" for rel in post_changes)
            + ".",
            FIX["scope"],
        )

    # Re-check the whole head tree so a maintainer pull request cannot land a broken sample.
    if not bot_expiry:
        from validator.posts import validate_tree

        known = {(issue.code, issue.path, issue.message) for issue in issues}
        for issue in validate_tree(head, today=today):
            key = (issue.code, issue.path, issue.message)
            if key in known or issue.code in {"ownership", "example"}:
                continue
            issues.append(issue)
            known.add(key)

    if scope_issue is not None:
        issues.append(scope_issue)
    notes: list[str] = []
    automerge = False
    if not issues and bot_ready:
        automerge = True
        notes.append(
            "This is the expiry workflow removing posts that are already past their expiry date. "
            "It can be squash-merged."
        )
    elif not issues and maintainer_pr:
        notes.append(
            "This pull request changes files outside `jobs/`, `talents/`, and `companies/`. "
            "Post checks passed. Auto-merge stays off; a maintainer (`@zwobill`) needs to merge it."
        )
    elif not issues:
        automerge = True
        notes.append(
            "Checks passed and the pull request touches one post. "
            "It can be squash-merged with the GitHub Actions token."
        )
    return Result(issues=issues, notes=notes, automerge=automerge)


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


def _single_submission(
    added: list[str],
    modified: list[str],
    deleted: list[str],
    head: Path,
    base_files: dict[str, Path],
) -> bool:
    if len(modified) == 1 and not added and not deleted:
        return True
    if len(added) == 1 and not modified and not deleted:
        return True
    if len(deleted) == 1 and not modified and not added:
        return True
    if len(added) == 1 and len(deleted) == 1 and not modified:
        try:
            new_meta, _body = load_post(head / added[0])
            old_meta, _old = load_post(base_files[deleted[0]])
        except (OSError, PostParseError, KeyError):
            return False
        return _same_family(old_meta.get("kind"), new_meta.get("kind")) and owner_of(old_meta) == owner_of(
            new_meta
        )
    return False


def _same_family(left: object, right: object) -> bool:
    talents = {"talent", "talent-ref"}
    if left in talents and right in talents:
        return True
    return left == right and left in {"job", "company", "talent", "talent-ref"}


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
