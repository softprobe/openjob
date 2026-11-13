"""Isolated copies of the three sample posts.

The samples are fixtures under ``tests/fixtures/samples/``. They are not live
posts. Tests that describe them copy the fixtures into a temporary tree whose
``jobs/``, ``talents/``, and ``companies/`` directories look like a repository.
Indexing the live repository would fail as soon as a real post is merged, or
when a post's date is outside the frozen day the tests use.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "samples"

SAMPLES = (
    "jobs/2026/11/example-studio-open-source-maintainer.md",
    "talents/z/zwobill.md",
    "companies/e/example-studio.md",
)


def sample_tree() -> Path:
    root = Path(tempfile.mkdtemp())
    for rel in SAMPLES:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURES / rel, dest)
    return root
