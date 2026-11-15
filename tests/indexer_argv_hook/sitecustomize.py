"""Test-only fetch stand-in. Loaded when this directory is on PYTHONPATH.

``python -m indexer`` reimports the package after site startup, so the patch
is applied on every import of ``indexer.run``.
"""

from __future__ import annotations

import builtins
import os
import sys

_import = builtins.__import__


def _job(job_id: str) -> dict:
    return {
        "id": job_id,
        "title": "Engineer",
        "company": "Acme",
        "location": "Remote",
        "remote": "remote",
        "department": "",
        "employment_type": "FULL_TIME",
        "salary_text": "",
        "salary_source": "",
        "posted": "2026-11-01",
        "updated": "",
        "deadline": "",
        "source_url": f"https://boards.example/{job_id}",
        "apply_url": f"https://boards.example/{job_id}",
    }


def fetch(source, etag=None):
    if os.environ.get("OPENJOB_INDEX_FIXTURE") == "empty":
        return {"ok": True, "jobs": [], "etag": None}
    return {"ok": True, "jobs": [_job(source["slug"])], "etag": None}


def _hooked(name, globals=None, locals=None, fromlist=(), level=0):
    module = _import(name, globals, locals, fromlist, level)
    runner = sys.modules.get("indexer.run")
    spec = getattr(runner, "__spec__", None)
    if spec is not None and getattr(spec, "_initializing", False):
        return module
    if runner is None or getattr(runner, "__spec__", None) is None:
        return module
    defaults = getattr(runner.run, "__kwdefaults__", None)
    if defaults is not None and defaults.get("fetch") is not fetch:
        defaults["fetch"] = fetch
    return module


builtins.__import__ = _hooked
