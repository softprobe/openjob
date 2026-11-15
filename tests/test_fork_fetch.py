"""A fork pull request is fetched as data, and a missing tree is not a deletion."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from validator.pr import check_pr

from tests.test_ownership import _company, _job, _tree

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "automerge.yml"


class WorkflowTests(unittest.TestCase):
    def test_trusted_validate_fetches_the_pull_ref_without_a_token(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('fetch --depth=1 origin "refs/pull/${PR_NUMBER}/head"', text)
        self.assertIn("-c credential.helper=", text)
        self.assertNotIn("allow-unsafe-pr-checkout", text)
        self.assertIn("steps.head.outcome == 'success'", text)
        self.assertIn("working-directory: base", text)
        self.assertIn("pip install -r base/requirements.txt", text)
        self.assertIn("python -m validator check-pr", text)
        self.assertIn("--head ../head", text)
        head = text.index("HEAD_OUTCOME !== \"success\"")
        report = text.index("readFileSync(process.env.REPORT", head)
        self.assertLess(head, report)
        self.assertIn("No post was judged.", text)


class MissingTreeTests(unittest.TestCase):
    def test_a_missing_head_does_not_accuse_anyone_of_deleting_a_post(self) -> None:
        base = _tree(
            {
                "companies/s/softprobe.md": _company(slug="softprobe", posted_by="zwobill", owners=["lcunsp", "zwobill"]),
                "jobs/2026/11/softprobe-software-engineer.md": _job(
                    company="softprobe",
                    company_name="Softprobe",
                    role_slug="software-engineer",
                    posted_by="zwobill",
                    apply="mailto:hr@softprobe.ai",
                ),
            }
        )
        missing = base.parent / "missing-head"
        try:
            result = check_pr(head=missing, base=base, author="ShahadatTest")
        finally:
            shutil.rmtree(base)
        self.assertEqual([issue.code for issue in result.issues], ["checkout"])
        self.assertNotIn("cannot remove", result.report())
        self.assertNotIn("softprobe.md", result.report())


class ForkFetchTests(unittest.TestCase):
    def test_the_pull_ref_shows_the_fork_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin.git"
            base = root / "base"
            fork = root / "fork"
            fetched = root / "fetched"
            _git("init", "--bare", "-b", "main", str(origin))
            _git("init", "-b", "main", str(base))
            (base / "companies" / "s").mkdir(parents=True)
            (base / "jobs" / "2026" / "11").mkdir(parents=True)
            (base / "site").mkdir()
            company = _company(slug="softprobe", posted_by="zwobill", owners=["lcunsp", "zwobill"])
            job = _job(
                company="softprobe",
                company_name="Softprobe",
                role_slug="software-engineer",
                posted_by="zwobill",
                apply="https://www.softprobe.ai/jobs/software-engineer",
            )
            (base / "companies" / "s" / "softprobe.md").write_text(company, encoding="utf-8")
            (base / "jobs" / "2026" / "11" / "softprobe-software-engineer.md").write_text(job, encoding="utf-8")
            (base / "site" / "app.js").write_text("var live = 1;\n", encoding="utf-8")
            _git("-C", str(base), "add", ".")
            _git("-C", str(base), "commit", "-m", "base")
            _git("-C", str(base), "remote", "add", "origin", str(origin))
            _git("-C", str(base), "push", "origin", "main")
            _git("clone", str(origin), str(fork))
            app = fork / "site" / "app.js"
            app.write_text("var live = 2;\n", encoding="utf-8")
            _git("-C", str(fork), "add", "site/app.js")
            _git("-C", str(fork), "commit", "-m", "fork change")
            sha = _git("-C", str(fork), "rev-parse", "HEAD").stdout.strip()
            _git("-C", str(fork), "push", str(origin), f"HEAD:refs/pull/40/head")

            _git("init", "-b", "main", str(fetched))
            _git("-C", str(fetched), "remote", "add", "origin", str(origin))
            _git(
                "-C",
                str(fetched),
                "-c",
                "credential.helper=",
                "-c",
                "http.extraheader=",
                "fetch",
                "--depth=1",
                "origin",
                "refs/pull/40/head",
            )
            _git("-C", str(fetched), "checkout", "--detach", "FETCH_HEAD")
            self.assertEqual(_git("-C", str(fetched), "rev-parse", "HEAD").stdout.strip(), sha)
            shutil.rmtree(fetched / ".git")
            result = check_pr(head=fetched, base=base, author="ShahadatTest", today=date(2026, 11, 14))
            report = result.report()
            self.assertEqual(result.issues, [], [f"{issue.code}: {issue.path}: {issue.message}" for issue in result.issues])
            self.assertIn("site/app.js", report)
            self.assertNotIn("cannot remove", report)
            self.assertFalse(result.automerge)


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=OpenJob Test",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
