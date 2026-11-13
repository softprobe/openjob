"""Command line entry points used by GitHub Actions and local checks."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from validator.expire import apply_removals, render_expiry_report, select_expired
from validator.index import build_index
from validator.posts import validate_tree
from validator.pr import check_pr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m validator")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-pr", help="validate a pull request tree against its base")
    check.add_argument("--head", type=Path, required=True)
    check.add_argument("--base", type=Path, required=True)
    check.add_argument("--author", required=True)
    check.add_argument("--today")
    check.add_argument("--report", type=Path)
    check.add_argument("--github-output", type=Path)

    tree = sub.add_parser("check-tree", help="validate every live post")
    tree.add_argument("--root", type=Path, default=Path("."))
    tree.add_argument("--today")

    index = sub.add_parser("build-index", help="write the public JSON index")
    index.add_argument("--root", type=Path, default=Path("."))
    index.add_argument("--out", type=Path, required=True)
    index.add_argument("--today")

    expire = sub.add_parser("expire", help="list or delete expired posts")
    expire.add_argument("--root", type=Path, default=Path("."))
    expire.add_argument("--today")
    expire.add_argument("--apply", action="store_true")
    expire.add_argument("--report", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "check-pr":
            return _check_pr(args)
        if args.command == "check-tree":
            return _check_tree(args)
        if args.command == "build-index":
            return _build_index(args)
        if args.command == "expire":
            return _expire(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 2


def _check_pr(args: argparse.Namespace) -> int:
    result = check_pr(
        head=args.head,
        base=args.base,
        author=args.author,
        today=_today(args.today),
    )
    report = result.report()
    sys.stdout.write(report)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"automerge={'true' if result.automerge else 'false'}\n")
    return 1 if result.issues else 0


def _check_tree(args: argparse.Namespace) -> int:
    issues = validate_tree(args.root, today=_today(args.today))
    if not issues:
        print(f"OK {args.root}")
        return 0
    for issue in issues:
        print(f"[{issue.code}] {issue.path}: {issue.message}")
    return 1


def _build_index(args: argparse.Namespace) -> int:
    document = build_index(args.root, today=_today(args.today))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(document['posts'])} posts to {args.out}")
    return 0


def _expire(args: argparse.Namespace) -> int:
    today = _today(args.today)
    expired = select_expired(args.root, today=today)
    if args.apply:
        apply_removals(args.root, expired)
    report = render_expiry_report(expired, today=today)
    sys.stdout.write(report)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    return 0


def _today(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(timezone.utc).date()


if __name__ == "__main__":
    raise SystemExit(main())
