"""Isolated copies of the three sample posts.

Tests that describe the samples use this tree. Indexing the live repository
would fail as soon as a real post is merged, or when a post's date is outside
the frozen day the tests use.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
        shutil.copy(ROOT / rel, dest)
    return root
