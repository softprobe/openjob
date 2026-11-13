"""Privacy fixtures and the narrow allow-list."""

from __future__ import annotations

import unittest
from pathlib import Path

from validator.privacy import find_contacts

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "privacy"


def kinds(text: str) -> set[str]:
    return {finding.kind for finding in find_contacts(text)}


class PrivacyFixtureTests(unittest.TestCase):
    def test_rejects_plain_email(self) -> None:
        self.assertIn("email", kinds((FIXTURES / "email.md").read_text(encoding="utf-8")))

    def test_rejects_obfuscated_email(self) -> None:
        text = (FIXTURES / "email-obfuscated.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            with self.subTest(line=line):
                self.assertIn("email", kinds(line), line)

    def test_rejects_chinese_and_spaced_phones(self) -> None:
        text = (FIXTURES / "phone-cn.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            with self.subTest(line=line):
                self.assertIn("phone", kinds(line), line)

    def test_rejects_international_phones(self) -> None:
        text = (FIXTURES / "phone-intl.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            with self.subTest(line=line):
                self.assertIn("phone", kinds(line), line)

    def test_clean_fixture_has_no_contacts(self) -> None:
        text = (FIXTURES / "clean.md").read_text(encoding="utf-8")
        self.assertEqual(find_contacts(text), [])

    def test_allows_documentation_domains_only(self) -> None:
        self.assertEqual(find_contacts("Write me [at] example [dot] com"), [])
        self.assertIn("email", kinds("Write me [at] gmail [dot] com"))

    def test_allows_fictional_nanp_and_rejects_copied_mobile(self) -> None:
        self.assertEqual(find_contacts("Call (415) 555-0100 in fiction."), [])
        self.assertIn("phone", kinds("13800138000"))
        self.assertIn("phone", kinds("Call (415) 555-2671."))

    def test_hidden_character_splits_an_email(self) -> None:
        found = find_contacts("a\u200bda@gmail.com")
        self.assertIn("email", {item.kind for item in found})
        self.assertIn("hidden", {item.kind for item in found})

    def test_redacts_the_address_in_the_detail(self) -> None:
        found = find_contacts("ada@gmail.com")
        self.assertTrue(found)
        self.assertNotIn("ada@gmail.com", found[0].detail)
        self.assertIn("gmail.com", found[0].detail)


if __name__ == "__main__":
    unittest.main()
