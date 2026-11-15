"""The reviewed source list is real boards, not a placeholder."""

from __future__ import annotations

import unittest
from pathlib import Path

from indexer.sources import load_sources

ROOT = Path(__file__).resolve().parents[1]


class SourceSeedTests(unittest.TestCase):
    def test_the_seed_list_loads(self) -> None:
        found = load_sources(ROOT / "sources")
        self.assertGreaterEqual(len(found), 50)
        slugs = [item["slug"] for item in found]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn("anthropic", slugs)
        self.assertIn("openai", slugs)
        self.assertIn("huggingface", slugs)
        self.assertTrue(all(item["ats"] in {"greenhouse", "lever", "ashby", "workable"} for item in found))


if __name__ == "__main__":
    unittest.main()
