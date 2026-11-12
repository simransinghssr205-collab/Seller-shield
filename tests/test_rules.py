"""Checks the rule checker against the 15 sample buyer messages.

Run from the project folder:
    venv\\Scripts\\python.exe -m unittest tests.test_rules
"""
import csv
import os
import unittest

from backend.risk_rules import check_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "sample_messages.csv")


class SampleMessages(unittest.TestCase):
    def test_every_sample_gets_the_expected_verdict(self):
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 15)
        for row in rows:
            with self.subTest(id=row["id"]):
                got = check_rules(row["message"])["verdict"]
                self.assertEqual(got, row["expected"], row["message"])

    def test_empty_message_is_safe(self):
        self.assertEqual(check_rules("")["verdict"], "safe")
        self.assertEqual(check_rules(None)["verdict"], "safe")


if __name__ == "__main__":
    unittest.main()
