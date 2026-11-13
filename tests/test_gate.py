"""Auto-merge proceeds only when Validate succeeded for the same commit."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validator.gate import merge_allowed, refusal_comment

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40
OTHER = "b" * 40


class MergeGateTests(unittest.TestCase):
    def test_success_on_the_same_sha_is_the_only_merge(self) -> None:
        self.assertTrue(
            merge_allowed(
                automerge=True,
                validate_conclusion="success",
                validate_sha=SHA,
                head_sha=SHA,
            )
        )

    def test_a_failing_or_missing_validate_blocks_the_merge(self) -> None:
        blocked = [
            "failure",
            "cancelled",
            "skipped",
            "timed_out",
            "neutral",
            "action_required",
            "startup_failure",
            "",
            None,
            "SUCCESS",
        ]
        for conclusion in blocked:
            with self.subTest(conclusion=conclusion):
                self.assertFalse(
                    merge_allowed(
                        automerge=True,
                        validate_conclusion=conclusion,
                        validate_sha=SHA,
                        head_sha=SHA,
                    )
                )

    def test_a_different_sha_blocks_the_merge(self) -> None:
        self.assertFalse(
            merge_allowed(
                automerge=True,
                validate_conclusion="success",
                validate_sha=OTHER,
                head_sha=SHA,
            )
        )
        self.assertFalse(
            merge_allowed(
                automerge=True,
                validate_conclusion="success",
                validate_sha="",
                head_sha=SHA,
            )
        )

    def test_the_trusted_checker_can_refuse_a_green_validate(self) -> None:
        self.assertFalse(
            merge_allowed(
                automerge=False,
                validate_conclusion="success",
                validate_sha=SHA,
                head_sha=SHA,
            )
        )

    def test_refusal_comment_names_the_commit_and_stays_open(self) -> None:
        text = refusal_comment(
            head_sha=SHA,
            validate_conclusion="failure",
            validate_sha=SHA,
        )
        self.assertIn("<!-- openjob-merge-gate -->", text)
        self.assertIn("left this pull request open", text)
        self.assertIn(SHA, text)
        self.assertIn("`failure`", text)
        self.assertIn("specific fix", text)

    def test_surrounding_whitespace_does_not_hide_a_real_success(self) -> None:
        self.assertTrue(
            merge_allowed(
                automerge=True,
                validate_conclusion="success\n",
                validate_sha=SHA,
                head_sha=SHA,
            )
        )

    def test_cli_refuses_a_failed_validate_and_allows_success(self) -> None:
        refused = _gate("failure", SHA, SHA)
        try:
            self.assertEqual(refused.returncode, 1, refused.stderr)
            self.assertIn("left this pull request open", refused.stdout)
            self.assertIn(
                "<!-- openjob-merge-gate -->",
                Path(refused.comment).read_text(encoding="utf-8"),
            )
        finally:
            Path(refused.comment).unlink(missing_ok=True)
        allowed = _gate("success", SHA, SHA)
        try:
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertFalse(Path(allowed.comment).exists())
        finally:
            Path(allowed.comment).unlink(missing_ok=True)


class WorkflowWiringTests(unittest.TestCase):
    def test_squash_merge_comes_after_the_gate(self) -> None:
        text = (ROOT / ".github/workflows/automerge.yml").read_text(encoding="utf-8")
        gate = text.index("python -m validator merge-gate")
        merge = text.index("pulls.merge")
        self.assertLess(gate, merge)
        self.assertIn("needs.trusted-validate.result == 'success'", text)
        self.assertIn("sha,", text)
        self.assertIn("check_name: \"validate\"", text)


class _Result:
    def __init__(self, completed: subprocess.CompletedProcess[str], comment: str) -> None:
        self.returncode = completed.returncode
        self.stdout = completed.stdout
        self.stderr = completed.stderr
        self.comment = comment


def _gate(conclusion: str, validate_sha: str, head_sha: str) -> _Result:
    handle = tempfile.NamedTemporaryFile(prefix="openjob-gate-", suffix=".md", delete=False)
    comment = handle.name
    handle.close()
    Path(comment).unlink()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "validator",
            "merge-gate",
            "--automerge",
            "true",
            "--validate-conclusion",
            conclusion,
            "--validate-sha",
            validate_sha,
            "--head-sha",
            head_sha,
            "--comment",
            comment,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return _Result(completed, comment)
