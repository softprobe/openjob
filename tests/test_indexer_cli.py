"""The workflow command is `python -m indexer run ...`. Exit 2 is not a hold."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = Path(__file__).resolve().parent / "indexer_argv_hook"
ARGV = ["-m", "indexer", "run", "--sources", "sources", "--data", "../data", "--root", "."]


class WorkflowArgvTests(unittest.TestCase):
    def test_the_workflow_command_publishes_a_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, data = _layout(Path(tmp), jobs=0)
            result = _invoke(repo, fixture="one")
            report = json.loads((data / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("companies 1 jobs 1 publish true", result.stdout)
            self.assertTrue(report["publish"])
            self.assertTrue((data / "shards" / "greenhouse" / "acme.json").is_file())

    def test_a_sharp_drop_exits_3_and_writes_publish_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, data = _layout(Path(tmp), jobs=20)
            result = _invoke(repo, fixture="empty")
            report = json.loads((data / "report.json").read_text(encoding="utf-8"))
            kept = json.loads((data / "shards" / "greenhouse" / "acme.json").read_text(encoding="utf-8"))
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertIn("publish false", result.stdout)
            self.assertIs(report["publish"], False)
            self.assertEqual(len(kept["jobs"]), 20)

    def test_a_missing_subcommand_is_an_argparse_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, data = _layout(Path(tmp), jobs=0)
            result = _invoke(repo, argv=["-m", "indexer", "--sources", "sources", "--data", "../data", "--root", "."])
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("error:", result.stderr)
            self.assertFalse((data / "report.json").exists())


def _layout(tmp: Path, *, jobs: int) -> tuple[Path, Path]:
    repo = tmp / "repo"
    data = tmp / "data"
    sources = repo / "sources"
    sources.mkdir(parents=True)
    data.mkdir()
    (sources / "acme.yml").write_text(
        "slug: acme\nname: Acme\nwebsite: https://acme.example\nats: greenhouse\nboard: acme\n",
        encoding="utf-8",
    )
    (sources / "denylist.yml").write_text("boards: []\n", encoding="utf-8")
    if jobs:
        shard = data / "shards" / "greenhouse"
        shard.mkdir(parents=True)
        (shard / "acme.json").write_text(
            json.dumps(
                {
                    "ats": "greenhouse",
                    "board": "acme",
                    "slug": "acme",
                    "status": "ok",
                    "checked_at": "2026-11-14T06:00:00Z",
                    "failed_at": None,
                    "jobs": [{"id": str(number), "title": "Engineer"} for number in range(jobs)],
                }
            ),
            encoding="utf-8",
        )
    return repo, data


def _invoke(repo: Path, *, fixture: str = "one", argv: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(HOOK), str(ROOT), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    env["OPENJOB_INDEX_FIXTURE"] = fixture
    return subprocess.run(
        [sys.executable, *(argv or ARGV)],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


if __name__ == "__main__":
    unittest.main()
