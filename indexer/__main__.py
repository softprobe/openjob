"""Fetch public boards and write the data-branch shards.

The workflow command is ``python -m indexer run --sources sources --data ../data --root .``.

Exit 0 when the snapshot should be published. Exit 3 when a sharp drop holds
the publish; ``report.json`` then has ``publish`` set to false. Argparse
errors exit 2 and must fail the job.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from indexer.run import run

# Distinct from argparse's exit code 2.
HOLD_EXIT = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index public employer job feeds.")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("run", help="Fetch the reviewed boards and write shards.")
    fetch.add_argument("--sources", type=Path, default=Path("sources"))
    fetch.add_argument("--data", type=Path, required=True)
    fetch.add_argument("--root", type=Path, default=Path("."))
    fetch.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print counts. Write the snapshot under /tmp/openjob-index-dry-run.",
    )
    args = parser.parse_args(argv)
    data = Path("/tmp/openjob-index-dry-run") if args.dry_run else args.data
    report = run(args.sources, data, root=args.root, sleep=time.sleep)
    print(
        f"companies {report['companies']} jobs {report['jobs']} "
        f"publish {str(report['publish']).lower()}"
    )
    if not report["publish"]:
        return HOLD_EXIT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
