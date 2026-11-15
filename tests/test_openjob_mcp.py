"""OpenJob MCP tools: search, validate, and a pull request that stays off GitHub."""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
sys.path.insert(0, str(ROOT / "cli"))

from openjob_mcp.github import GitHubError  # noqa: E402
from openjob_mcp.index_client import get_job, get_talent, search_jobs, search_talent  # noqa: E402
from openjob_mcp.server import handle, read_message, write_message  # noqa: E402
from openjob_mcp.tools import TOOLS, close_job, create_or_update_post  # noqa: E402


POSTS = [
    {
        "kind": "job",
        "path": "jobs/2026/11/softprobe-software-engineer.md",
        "permalink": "https://openjob.softprobe.ai/p/jobs/2026/11/softprobe-software-engineer/",
        "title": "Software Engineer",
        "org": "Softprobe",
        "location": "Los Altos, California, USA",
        "remote": "hybrid",
        "languages": ["en"],
        "tags": ["ai-agents"],
        "apply_email": "mailto:hr@softprobe.ai",
        "owner": "zwobill",
        "excerpt": "AI agent observability",
    },
    {
        "kind": "talent",
        "path": "talents/ada.md",
        "permalink": "https://openjob.softprobe.ai/p/talents/ada/",
        "title": "Ada Lovelace",
        "owner": "ada",
        "location": "Berlin",
        "remote": "remote",
        "languages": ["en"],
        "tags": ["distributed-systems"],
        "open_to": ["full-time"],
        "headline": "Distributed systems engineer",
    },
]


def _job_fields() -> dict:
    return {
        "title": "Backend engineer",
        "company": "acme",
        "company_name": "Acme",
        "role_slug": "backend-engineer",
        "location": "Example City",
        "remote": True,
        "languages": ["en"],
        "tags": ["backend"],
        "apply": "https://example.com/jobs/backend-engineer",
        "posted_by": "ada",
        "body": "Describe the work, the team, and the location without a phone number or an email address.\n",
    }


def _talent_fields() -> dict:
    return {
        "name": "Ada Lovelace",
        "github": "someone-else",
        "headline": "Distributed systems engineer",
        "location": "Berlin",
        "remote": True,
        "languages": ["en"],
        "tags": ["distributed-systems"],
        "open_to": ["full-time"],
        "body": "I build reliable services and I am open to a full-time role. Contact is this GitHub login.\n",
    }


class SearchTests(unittest.TestCase):
    def test_tool_names(self) -> None:
        self.assertEqual(
            [tool["name"] for tool in TOOLS],
            [
                "search_jobs",
                "get_job",
                "search_talent",
                "get_talent",
                "validate_post",
                "create_or_update_post",
                "close_job",
            ],
        )

    def test_search_and_get_use_the_index_fields(self) -> None:
        jobs = search_jobs("observability", {"remote": "hybrid", "tag": "ai-agents"}, posts=POSTS)
        self.assertEqual(jobs[0]["path"], "jobs/2026/11/softprobe-software-engineer.md")
        self.assertEqual(len(search_jobs("", {"location": "Berlin"}, posts=POSTS)), 0)
        found = get_job("https://openjob.softprobe.ai/p/jobs/2026/11/softprobe-software-engineer/", posts=POSTS)
        self.assertEqual(found["apply_email"], "mailto:hr@softprobe.ai")
        self.assertEqual(get_talent("Ada", posts=POSTS)["headline"], "Distributed systems engineer")
        self.assertEqual(search_talent("", {"open_to": "full-time"}, posts=POSTS)[0]["owner"], "ada")


class PostTests(unittest.TestCase):
    def test_dry_run_validates_generated_job_and_talent_without_github(self) -> None:
        job = create_or_update_post("job", _job_fields(), dry_run=True, author="ada")
        talent = create_or_update_post("talent", _talent_fields(), dry_run=True, author="ada")
        self.assertTrue(job["ok"], job.get("issues"))
        self.assertTrue(talent["ok"], talent.get("issues"))
        self.assertTrue(job["path"].startswith("jobs/"))
        self.assertTrue(job["path"].endswith("/acme-backend-engineer.md"))
        self.assertEqual(talent["path"], "talents/ada.md")
        self.assertIn("posted_by: ada", job["markdown"])
        self.assertIn("github: ada", talent["markdown"])
        self.assertNotIn("someone-else", talent["markdown"])
        self.assertIsNone(job["pull_request"])
        self.assertIsNone(talent["pull_request"])

    def test_invalid_post_does_not_open_a_pull_request(self) -> None:
        calls: list[str] = []

        def transport(method: str, path: str, body: dict | None):
            calls.append(path)
            if path == "/user":
                return {"login": "ada"}
            raise AssertionError(path)

        os.environ["GITHUB_TOKEN"] = "test-token"
        try:
            result = create_or_update_post("job", {"title": "Too thin"}, dry_run=False, github=_client(transport))
        finally:
            os.environ.pop("GITHUB_TOKEN", None)
        self.assertFalse(result["ok"])
        self.assertEqual(calls, ["/user"])

    def test_write_opens_one_pull_request_on_a_fork(self) -> None:
        calls: list[tuple[str, str]] = []

        def transport(method: str, path: str, body: dict | None):
            calls.append((method, path.split("?", 1)[0]))
            if path == "/user":
                return {"login": "ada"}
            if path == "/repos/softprobe/openjob":
                return {"default_branch": "main", "permissions": {"push": False}}
            if path == "/repos/ada/openjob" and method == "GET":
                if not any(item == ("POST", "/repos/softprobe/openjob/forks") for item in calls):
                    raise GitHubError(404, "missing", path)
                return {"full_name": "ada/openjob"}
            if path == "/repos/softprobe/openjob/forks":
                return {"full_name": "ada/openjob"}
            if path == "/repos/softprobe/openjob/commits/main":
                return {"sha": "abc123"}
            if path.startswith("/repos/softprobe/openjob/contents/"):
                raise GitHubError(404, "new file", path)
            if path == "/repos/ada/openjob/git/refs":
                return {"ref": body["ref"]}
            if method == "PUT" and path.startswith("/repos/ada/openjob/contents/"):
                self.assertNotIn("\n", body["content"][:8])
                return {"content": {"path": path}}
            if path == "/repos/softprobe/openjob/pulls":
                self.assertEqual(body["base"], "main")
                self.assertTrue(body["head"].startswith("ada:openjob/"))
                return {"html_url": "https://github.com/softprobe/openjob/pull/99", "number": 99}
            if method == "DELETE":
                raise AssertionError("a new post is not a delete")
            raise AssertionError((method, path))

        result = create_or_update_post("job", _job_fields(), dry_run=False, github=_client(transport))
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["pull_request"]["number"], 99)
        methods = [method for method, path in calls if path == "/repos/softprobe/openjob/pulls"]
        self.assertEqual(methods, ["POST"])
        puts = [path for method, path in calls if method == "PUT"]
        self.assertEqual(len(puts), 1)

    def test_close_dry_run_names_the_job_file(self) -> None:
        result = close_job(
            "https://openjob.softprobe.ai/p/jobs/2026/11/softprobe-software-engineer/",
            dry_run=True,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "delete")
        self.assertEqual(result["path"], "jobs/2026/11/softprobe-software-engineer.md")
        self.assertIsNone(result["pull_request"])


class ProtocolTests(unittest.TestCase):
    def test_stdio_lists_tools_and_validates(self) -> None:
        inbound = io.BytesIO()
        write_message(inbound, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        write_message(inbound, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        write_message(inbound, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        job = create_or_update_post("job", _job_fields(), dry_run=True)
        write_message(
            inbound,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "validate_post",
                    "arguments": {"kind": "job", "markdown": job["markdown"]},
                },
            },
        )
        inbound.seek(0)
        self.assertEqual(read_message(inbound)["method"], "initialize")
        inbound.seek(0)
        responses = []
        while True:
            message = read_message(inbound)
            if message is None:
                break
            response = handle(message)
            if response is not None:
                responses.append(response)
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "openjob")
        names = [tool["name"] for tool in responses[1]["result"]["tools"]]
        self.assertIn("search_jobs", names)
        payload = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertTrue(payload["ok"], payload)


class LiveIndexTests(unittest.TestCase):
    def test_live_index_finds_the_softprobe_role(self) -> None:
        jobs = search_jobs("softprobe")
        paths = [job.get("path") for job in jobs]
        self.assertIn("jobs/2026/11/softprobe-software-engineer.md", paths)


def _client(transport):
    from openjob_mcp.github import GitHub

    return GitHub("test-token", transport=transport)


if __name__ == "__main__":
    unittest.main()
