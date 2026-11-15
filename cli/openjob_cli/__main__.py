"""`openjob` commands. Search needs no token. Writing needs GITHUB_TOKEN."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openjob_mcp.tools import close_job, create_or_update_post, validate_markdown
from openjob_mcp.index_client import get_job, get_talent, search_jobs, search_talent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openjob", description="Search OpenJob and open a pull request for one post.")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search-jobs", help="Search live jobs")
    search.add_argument("query", nargs="?", default="")
    _filter_args(search)

    one = sub.add_parser("get-job", help="Fetch one job")
    one.add_argument("id")

    talent = sub.add_parser("search-talent", help="Search live profiles")
    talent.add_argument("query", nargs="?", default="")
    _filter_args(talent)

    who = sub.add_parser("get-talent", help="Fetch one profile")
    who.add_argument("login")

    check = sub.add_parser("validate", help="Check a Markdown file")
    check.add_argument("kind", choices=("job", "talent", "company"))
    check.add_argument("file")

    post = sub.add_parser("post", help="Build a post and open a pull request")
    post.add_argument("kind", choices=("job", "talent", "company"))
    post.add_argument("--fields", required=True, help="JSON file of front-matter fields plus body")
    post.add_argument("--dry-run", action="store_true")

    close = sub.add_parser("close", help="Open a pull request that removes a job")
    close.add_argument("id")
    close.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    filters = {
        key: getattr(args, key)
        for key in ("location", "remote", "language", "tag", "employment_type", "open_to", "origin")
        if getattr(args, key, None)
    }
    if args.command == "search-jobs":
        payload = search_jobs(args.query, filters)
    elif args.command == "get-job":
        payload = get_job(args.id)
    elif args.command == "search-talent":
        payload = search_talent(args.query, filters)
    elif args.command == "get-talent":
        payload = get_talent(args.login)
    elif args.command == "validate":
        markdown = Path(args.file).read_text(encoding="utf-8")
        issues = validate_markdown(args.kind, markdown)
        payload = {"ok": not issues, "issues": issues}
    elif args.command == "post":
        fields = json.loads(Path(args.fields).read_text(encoding="utf-8"))
        payload = create_or_update_post(args.kind, fields, dry_run=args.dry_run)
    else:
        payload = close_job(args.id, dry_run=args.dry_run)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    ok = True if not isinstance(payload, dict) else payload.get("ok", payload is not None)
    return 0 if ok else 1


def _filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--location")
    parser.add_argument("--remote")
    parser.add_argument("--language")
    parser.add_argument("--tag")
    parser.add_argument("--employment-type", dest="employment_type")
    parser.add_argument("--open-to", dest="open_to")
    parser.add_argument("--origin", choices=("owner", "indexed"))


if __name__ == "__main__":
    raise SystemExit(main())
