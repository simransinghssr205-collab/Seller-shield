"""Tests for the SellerShield routes. PayPal is faked, so no keys or network needed.

Run from the project folder:
    venv\\Scripts\\python.exe -m unittest tests.test_app
"""
import os
import unittest
from unittest.mock import patch

from backend import app as appmod

DANGER = "I accidentally overpaid. Please send back the difference via Western Union."
WARNING = "Can you message me on WhatsApp? It is easier to chat there."
SAFE = "Hi, is this still available? Can I pick it up tomorrow?"


def paypal_order(order_id, custom_id=None, status="CREATED", capture_id=None):
    unit = {
        "amount": {"currency_code": "USD", "value": "25.00"},
        "payee": {"email_address": "seller@example.com"},
    }
    if custom_id:
        unit["custom_id"] = custom_id
    if capture_id:
        unit["payments"] = {"captures": [{"id": capture_id}]}
    return {
        "id": order_id,
        "status": status,
        "links": [{"rel": "payer-action", "href": f"https://sandbox.paypal.com/x?token={order_id}"}],
        "purchase_units": [unit],
    }


class Routes(unittest.TestCase):
    def setUp(self):
        self._key = os.environ.pop("ANTHROPIC_API_KEY", None)
        appmod.ORDER_VERDICTS.clear()
        self.client = appmod.app.test_client()
        self.pp = appmod.paypal_client

    def tearDown(self):
        if self._key is not None:
            os.environ["ANTHROPIC_API_KEY"] = self._key

    def post(self, path, body=None):
        return self.client.post(path, json=body) if body is not None else self.client.post(path)

    def test_check_message(self):
        r = self.post("/api/check-message", {"message": DANGER})
        self.assertEqual(r.get_json()["verdict"], "danger")
        self.assertEqual(self.post("/api/check-message", {"message": "  "}).status_code, 400)

    def test_danger_is_blocked_before_paypal(self):
        with patch.object(self.pp, "create_order") as create:
            r = self.post("/api/create-order", {"message": DANGER, "amount": "25.00"})
        self.assertEqual(r.status_code, 403)
        self.assertTrue(r.get_json()["blocked"])
        create.assert_not_called()

    def test_verdict_is_stored_inside_the_paypal_order(self):
        with patch.object(self.pp, "create_order", return_value=paypal_order("O1")) as create:
            r = self.post("/api/create-order", {"message": WARNING, "amount": "30"})
        self.assertEqual(r.status_code, 200)
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["amount"], "30.00")
        self.assertTrue(kwargs["custom_id"].startswith("sellershield:warning:"))
        self.assertEqual(r.get_json()["approve_url"], "https://sandbox.paypal.com/x?token=O1")

    def test_bad_amounts_are_rejected(self):
        for bad in ("abc", "-5", "0", "1.234", "10; drop"):
            with self.subTest(amount=bad):
                self.assertEqual(self.post("/api/create-order", {"amount": bad}).status_code, 400)

    def test_warning_needs_confirmation_then_captures(self):
        appmod.ORDER_VERDICTS["O1"] = {"verdict": "warning", "score": 25, "reasons": []}
        done = paypal_order("O1", status="COMPLETED", capture_id="CAP1")
        with patch.object(self.pp, "capture_order", return_value=done) as capture:
            first = self.post("/api/order/O1/capture", {})
            capture.assert_not_called()
            second = self.post("/api/order/O1/capture", {"confirm": True})
        self.assertEqual(first.status_code, 409)
        self.assertTrue(first.get_json()["needs_confirmation"])
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.get_json()["capture_id"], "CAP1")

    def test_safe_captures_without_confirmation(self):
        appmod.ORDER_VERDICTS["O2"] = {"verdict": "safe", "score": 0, "reasons": []}
        with patch.object(self.pp, "capture_order", return_value=paypal_order("O2", capture_id="C2")):
            r = self.post("/api/order/O2/capture", {})
        self.assertEqual(r.status_code, 200)

    def test_verdict_survives_a_restart_because_it_is_in_the_paypal_order(self):
        # Memory is empty, as after a restart. PayPal still holds the verdict.
        stored = paypal_order("O3", custom_id="sellershield:warning:25")
        with patch.object(self.pp, "get_order", return_value=stored), \
             patch.object(self.pp, "capture_order") as capture:
            r = self.post("/api/order/O3/capture", {})
        self.assertEqual(r.status_code, 409)
        capture.assert_not_called()

    def test_danger_order_is_never_captured(self):
        stored = paypal_order("O4", custom_id="sellershield:danger:90")
        with patch.object(self.pp, "get_order", return_value=stored), \
             patch.object(self.pp, "capture_order") as capture:
            r = self.post("/api/order/O4/capture", {"confirm": True})
        self.assertEqual(r.status_code, 403)
        capture.assert_not_called()

    def test_orders_without_a_message_work_as_before(self):
        with patch.object(self.pp, "create_order", return_value=paypal_order("O5")) as create:
            r = self.post("/api/create-order")
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.get_json()["analysis"])
        self.assertIsNone(create.call_args.kwargs["custom_id"])
        self.assertNotIn("O5", appmod.ORDER_VERDICTS)

    def test_get_order_includes_details_and_verdict(self):
        stored = paypal_order("O6", custom_id="sellershield:safe:0", status="APPROVED")
        with patch.object(self.pp, "get_order", return_value=stored):
            j = self.client.get("/api/order/O6").get_json()
        self.assertEqual(j["details"]["amount"], "25.00")
        self.assertEqual(j["sellershield"]["verdict"], "safe")

    def test_refund(self):
        with patch.object(self.pp, "refund_capture", return_value={"id": "R1", "status": "COMPLETED"}) as refund:
            r = self.post("/api/capture/CAP1/refund")
        self.assertEqual(r.get_json()["status"], "COMPLETED")
        refund.assert_called_once_with("CAP1")

    def test_paypal_errors_come_back_as_500_with_the_message(self):
        with patch.object(self.pp, "create_order", side_effect=RuntimeError("PayPal returned 401")):
            r = self.post("/api/create-order", {"message": SAFE})
        self.assertEqual(r.status_code, 500)
        self.assertIn("401", r.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
