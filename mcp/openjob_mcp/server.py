"""Stdio MCP server for OpenJob. One JSON-RPC message per Content-Length frame or line."""

from __future__ import annotations

import json
import sys
from typing import BinaryIO

from openjob_mcp import __version__
from openjob_mcp.tools import TOOLS, call_tool

PROTOCOL = "2024-11-05"


def main() -> None:
    serve(sys.stdin.buffer, sys.stdout.buffer)


def serve(stdin: BinaryIO, stdout: BinaryIO) -> None:
    while True:
        message = read_message(stdin)
        if message is None:
            return
        response = handle(message)
        if response is not None:
            write_message(stdout, response)


def handle(message: dict) -> dict | None:
    method = message.get("method")
    identifier = message.get("id")
    if method == "notifications/initialized" or method is None and identifier is None:
        return None
    if identifier is None:
        return None
    if method == "initialize":
        params = message.get("params") or {}
        version = params.get("protocolVersion") or PROTOCOL
        return _result(
            identifier,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "openjob", "version": __version__},
            },
        )
    if method == "ping":
        return _result(identifier, {})
    if method == "tools/list":
        return _result(identifier, {"tools": list(TOOLS)})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            payload = call_tool(str(params.get("name") or ""), params.get("arguments") or {})
            text = json.dumps(payload, ensure_ascii=False, indent=2)
            return _result(
                identifier,
                {"content": [{"type": "text", "text": text}], "isError": not payload.get("ok", False)},
            )
        except Exception as exc:  # noqa: BLE001 — surface a tool failure to the client
            return _result(
                identifier,
                {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            )
    return {
        "jsonrpc": "2.0",
        "id": identifier,
        "error": {"code": -32601, "message": f"Unknown method {method}"},
    }


def read_message(stdin: BinaryIO) -> dict | None:
    header = b""
    while True:
        line = stdin.readline()
        if line == b"":
            return None
        if line in (b"\r\n", b"\n"):
            break
        header += line
        if line.startswith(b"{"):
            return json.loads(line.decode("utf-8"))
    length = 0
    for raw in header.splitlines():
        if raw.lower().startswith(b"content-length:"):
            length = int(raw.split(b":", 1)[1].strip())
    if length <= 0:
        return None
    body = stdin.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stdout: BinaryIO, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    stdout.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    stdout.flush()


def _result(identifier, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": identifier, "result": result}
