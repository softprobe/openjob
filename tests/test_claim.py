"""A well-known file can prove company owners. Anything else waits for a maintainer."""

from __future__ import annotations

import shutil
import unittest
from datetime import date

from validator.claim import fetch_well_known, well_known_url
from validator.posts import validate_tree
from validator.pr import check_pr

from tests.test_ownership import _company, _tree

TODAY = date(2026, 11, 14)


class ClaimTests(unittest.TestCase):
    def test_a_listed_owner_can_auto_merge_a_new_company(self) -> None:
        page = _company()
        head = _tree({"companies/a/acme.md": page})
        base = _tree({})
        try:
            result = check_pr(
                head=head,
                base=base,
                author="ada",
                today=TODAY,
                claim_fetch=lambda url: "ada\n",
            )
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertEqual(result.issues, [], [issue.message for issue in result.issues])
        self.assertTrue(result.automerge)
        self.assertEqual(
            well_known_url("https://example.com"),
            "https://example.com/.well-known/openjob.txt",
        )

    def test_a_missing_file_stays_with_the_maintainer(self) -> None:
        head = _tree({"companies/a/acme.md": _company()})
        base = _tree({})
        try:
            result = check_pr(
                head=head,
                base=base,
                author="ada",
                today=TODAY,
                claim_fetch=lambda url: "",
            )
        finally:
            shutil.rmtree(head)
            shutil.rmtree(base)
        self.assertFalse(result.automerge)
        self.assertIn("reviewed once", result.report())
        self.assertIn("well-known/openjob.txt", result.report())

    def test_private_and_local_hosts_are_not_fetched(self) -> None:
        self.assertIsNone(well_known_url("https://127.0.0.1/"))
        self.assertIsNone(well_known_url("https://localhost/"))
        self.assertIsNone(well_known_url("http://example.com/"))
        self.assertEqual(fetch_well_known("https://127.0.0.1/.well-known/openjob.txt"), "")

    def test_index_off_is_valid_company_front_matter(self) -> None:
        text = _company().replace("owners:\n- ada\n", 'owners:\n- ada\nindex: "off"\n')
        root = _tree({"companies/a/acme.md": text})
        try:
            issues = validate_tree(root, today=TODAY)
        finally:
            shutil.rmtree(root)
        self.assertEqual(issues, [], [issue.message for issue in issues])


if __name__ == "__main__":
    unittest.main()
