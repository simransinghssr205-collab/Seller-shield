"""Tests for the combined rules + AI analyzer. No network, no API key needed.

Run from the project folder:
    venv\\Scripts\\python.exe -m unittest tests.test_analyzer
"""
import os
import unittest
from unittest.mock import patch

from backend import analyzer, risk_rules

OVERPAY = "I accidentally overpaid. Please send back the difference via Western Union."
SAFE = "Hi, is this still available? Can I pick it up tomorrow?"
WARN = "Can you message me on WhatsApp? It is easier to chat there."


def ai_says(verdict, **extra):
    base = {
        "verdict": verdict,
        "scam_type": None,
        "reasons": [],
        "summary": None,
        "suggested_reply": None,
    }
    base.update(extra)
    return base


class Analyzer(unittest.TestCase):
    def setUp(self):
        self._key = os.environ.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self):
        if self._key is not None:
            os.environ["ANTHROPIC_API_KEY"] = self._key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_rules_only_scam_gets_type_and_reply(self):
        r = analyzer.analyze_message(OVERPAY)
        self.assertEqual(r["verdict"], "danger")
        self.assertFalse(r["ai_used"])
        self.assertEqual(r["scam_type"], "Overpayment scam")
        self.assertIn("exact listed price", r["suggested_reply"])

    def test_safe_message_has_no_type_or_reply(self):
        r = analyzer.analyze_message(SAFE)
        self.assertEqual(r["verdict"], "safe")
        self.assertIsNone(r["scam_type"])
        self.assertIsNone(r["suggested_reply"])

    def test_ai_can_raise_the_verdict_and_score_follows(self):
        with patch.object(analyzer.ai_checker, "ai_enabled", return_value=True), \
             patch.object(analyzer.ai_checker, "check_with_ai", return_value=ai_says(
                 "danger", scam_type="Refund scam", reasons=["Odd request"],
                 suggested_reply="Please pay the listed price.")):
            r = analyzer.analyze_message(SAFE)
        self.assertEqual(r["verdict"], "danger")
        self.assertGreaterEqual(r["score"], risk_rules.DANGER_AT)
        self.assertTrue(r["ai_used"])
        self.assertEqual(r["scam_type"], "Refund scam")
        self.assertEqual(r["suggested_reply"], "Please pay the listed price.")

    def test_ai_cannot_lower_a_rules_verdict(self):
        with patch.object(analyzer.ai_checker, "ai_enabled", return_value=True), \
             patch.object(analyzer.ai_checker, "check_with_ai", return_value=ai_says("safe")):
            r = analyzer.analyze_message(OVERPAY)
        self.assertEqual(r["verdict"], "danger")
        self.assertEqual(r["ai_verdict"], "safe")
        # AI gave no reply, so the rules' reply is used
        self.assertIn("exact listed price", r["suggested_reply"])

    def test_ai_failure_falls_back_to_rules(self):
        with patch.object(analyzer.ai_checker, "ai_enabled", return_value=True), \
             patch.object(analyzer.ai_checker, "check_with_ai", side_effect=RuntimeError("boom")):
            r = analyzer.analyze_message(WARN)
        self.assertEqual(r["verdict"], "warning")
        self.assertFalse(r["ai_used"])
        self.assertEqual(r["ai_error"], "boom")
        self.assertTrue(r["suggested_reply"])

    def test_flagged_by_ai_only_still_gets_a_reply(self):
        with patch.object(analyzer.ai_checker, "ai_enabled", return_value=True), \
             patch.object(analyzer.ai_checker, "check_with_ai", return_value=ai_says("warning")):
            r = analyzer.analyze_message(SAFE)
        self.assertEqual(r["suggested_reply"], risk_rules.GENERIC_REPLY)


if __name__ == "__main__":
    unittest.main()
