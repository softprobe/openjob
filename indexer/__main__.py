"""Fetch public boards and write the data-branch shards."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from indexer.run import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Index public employer job feeds.")
    parser.add_argument("--sources", type=Path, default=Path("sources"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print counts. Do not write shards.")
    args = parser.parse_args()
    if args.dry_run:
        report = run(args.sources, Path("/tmp/openjob-index-dry-run"), root=args.root, sleep=time.sleep)
        # A dry run still writes under a temp directory so the caller can inspect it.
        print(
            f"companies {report['companies']} jobs {report['jobs']} "
            f"publish {str(report['publish']).lower()}"
        )
        return
    report = run(args.sources, args.data, root=args.root, sleep=time.sleep)
    print(
        f"companies {report['companies']} jobs {report['jobs']} "
        f"publish {str(report['publish']).lower()}"
    )
    if not report["publish"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
