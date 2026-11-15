"""Open one pull request as the person whose token this is."""

from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from openjob_mcp.posts import UPSTREAM

API = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, status: int, message: str, path: str) -> None:
        super().__init__(f"GitHub {status} on {path}: {message}")
        self.status = status
        self.path = path


class GitHub:
    def __init__(self, token: str, transport=None) -> None:
        self.token = token
        self.transport = transport

    def request(self, method: str, path: str, body: dict | None = None):
        if self.transport is not None:
            return self.transport(method, path, body)
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(f"{API}{path}", data=data, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "openjob-mcp")
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise GitHubError(exc.code, detail, path) from exc
        if not raw:
            return {}
        return json.loads(raw)

    def login(self) -> str:
        payload = self.request("GET", "/user")
        login = payload.get("login")
        if not login:
            raise GitHubError(401, "The token did not return a login.", "/user")
        return str(login)

    def open_file_pr(self, *, path: str, content: str, title: str, body: str, delete: bool = False) -> dict:
        login = self.login()
        upstream = self.request("GET", f"/repos/{UPSTREAM}")
        default = str(upstream.get("default_branch") or "main")
        can_push = bool((upstream.get("permissions") or {}).get("push"))
        owner = UPSTREAM.split("/", 1)[0] if can_push else self._fork(login)
        base = self.request("GET", f"/repos/{UPSTREAM}/commits/{default}")
        sha = base["sha"]
        file_sha = self._file_sha(path, default)
        if delete and not file_sha:
            raise GitHubError(404, "That job is not on the default branch.", path)
        branch = _branch_name(path)
        self.request(
            "POST",
            f"/repos/{owner}/openjob/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )
        message = f"Close {path}" if delete else (f"Update {path}" if file_sha else f"Add {path}")
        if delete:
            self.request(
                "DELETE",
                f"/repos/{owner}/openjob/contents/{path}",
                {"message": message, "sha": file_sha, "branch": branch},
            )
        else:
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": branch,
            }
            if file_sha:
                payload["sha"] = file_sha
            self.request("PUT", f"/repos/{owner}/openjob/contents/{path}", payload)
        pull = self.request(
            "POST",
            f"/repos/{UPSTREAM}/pulls",
            {
                "title": title,
                "head": f"{owner}:{branch}",
                "base": default,
                "body": body,
            },
        )
        return {
            "url": pull.get("html_url"),
            "number": pull.get("number"),
            "path": path,
            "head": f"{owner}:{branch}",
        }

    def _fork(self, login: str) -> str:
        try:
            self.request("GET", f"/repos/{login}/openjob")
            return login
        except GitHubError as exc:
            if exc.status != 404:
                raise
        self.request("POST", f"/repos/{UPSTREAM}/forks", {})
        for _ in range(5):
            try:
                self.request("GET", f"/repos/{login}/openjob")
                return login
            except GitHubError as exc:
                if exc.status != 404:
                    raise
                if self.transport is None:
                    time.sleep(1)
        raise GitHubError(404, "The fork was not ready.", f"/repos/{login}/openjob")

    def file_text(self, path: str, ref: str) -> str | None:
        try:
            payload = self.request("GET", f"/repos/{UPSTREAM}/contents/{path}?ref={ref}")
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(payload, dict) or "content" not in payload:
            return None
        return base64.b64decode(payload["content"]).decode("utf-8")

    def _file_sha(self, path: str, ref: str) -> str | None:
        try:
            payload = self.request("GET", f"/repos/{UPSTREAM}/contents/{path}?ref={ref}")
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        if isinstance(payload, dict):
            return payload.get("sha")
        return None


def _branch_name(path: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")[:50]
    suffix = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"openjob/{stem}-{suffix}"
