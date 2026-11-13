"""Command line entry points used by GitHub Actions and local checks."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from validator.expire import apply_removals, render_expiry_report, select_expired
from validator.gate import merge_allowed, refusal_comment
from validator.index import build_index, write_pages
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
    index.add_argument("--pages", type=Path, help="site directory that receives p/<path>/index.html")
    index.add_argument("--today")

    expire = sub.add_parser("expire", help="list or delete expired posts")
    expire.add_argument("--root", type=Path, default=Path("."))
    expire.add_argument("--today")
    expire.add_argument("--apply", action="store_true")
    expire.add_argument("--report", type=Path)

    gate = sub.add_parser(
        "merge-gate",
        help="exit 0 only when auto-merge may proceed for this head SHA",
    )
    gate.add_argument("--automerge", required=True, choices=["true", "false"])
    gate.add_argument("--validate-conclusion", default="")
    gate.add_argument("--validate-sha", default="")
    gate.add_argument("--head-sha", default="")
    gate.add_argument("--comment", type=Path)

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
        if args.command == "merge-gate":
            return _merge_gate(args)
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
        payload = ""
        if result.share_comment:
            payload = base64.b64encode(result.share_comment.encode("utf-8")).decode("ascii")
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"automerge={'true' if result.automerge else 'false'}\n")
            handle.write(f"share_b64={payload}\n")
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
    if args.pages:
        count = write_pages(args.root, args.pages, document)
        print(f"Wrote {count} permalink pages under {args.pages / 'p'}")
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


def _merge_gate(args: argparse.Namespace) -> int:
    conclusion = args.validate_conclusion or None
    validate_sha = args.validate_sha or None
    head_sha = args.head_sha or None
    allowed = merge_allowed(
        automerge=args.automerge == "true",
        validate_conclusion=conclusion,
        validate_sha=validate_sha,
        head_sha=head_sha,
    )
    if allowed:
        print(f"merge allowed for {head_sha}")
        return 0
    text = refusal_comment(
        head_sha=head_sha,
        validate_conclusion=conclusion,
        validate_sha=validate_sha,
    )
    sys.stdout.write(text)
    if args.comment:
        args.comment.write_text(text, encoding="utf-8")
    return 1


def _today(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(timezone.utc).date()


if __name__ == "__main__":
    raise SystemExit(main())
