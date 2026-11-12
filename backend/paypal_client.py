import os
import uuid

import requests

from backend import config

TIMEOUT = 30

# Where PayPal sends the buyer back after approving or cancelling.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def _check_credentials():
    if not config.PAYPAL_CLIENT_ID or not config.PAYPAL_CLIENT_SECRET:
        raise ValueError(
            "Missing PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET in your .env file."
        )


def _check_response(resp):
    if not resp.ok:
        raise RuntimeError(f"PayPal returned {resp.status_code}: {resp.text}")


def _auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": str(uuid.uuid4()),
    }


def get_access_token():
    """Get a sandbox access token. Raises with PayPal's message on failure."""
    _check_credentials()

    resp = requests.post(
        f"{config.PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(config.PAYPAL_CLIENT_ID, config.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=TIMEOUT,
    )
    _check_response(resp)
    return resp.json()["access_token"]


def create_order(amount="10.00", currency="USD", custom_id=None, description=None):
    """Create a sandbox order. custom_id and description are stored inside the
    PayPal order itself, so SellerShield's verdict travels with the payment."""
    token = get_access_token()

    unit = {"amount": {"currency_code": currency, "value": amount}}
    if custom_id:
        unit["custom_id"] = custom_id
    if description:
        unit["description"] = description

    resp = requests.post(
        f"{config.PAYPAL_BASE_URL}/v2/checkout/orders",
        json={
            "intent": "CAPTURE",
            "purchase_units": [unit],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "user_action": "PAY_NOW",
                        "return_url": f"{FRONTEND_URL}/",
                        "cancel_url": f"{FRONTEND_URL}/?cancelled=1",
                    }
                }
            },
        },
        headers=_auth_headers(token),
        timeout=TIMEOUT,
    )
    _check_response(resp)
    return resp.json()


def get_order(order_id):
    """Fetch an order's current details and status."""
    token = get_access_token()

    resp = requests.get(
        f"{config.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT,
    )
    _check_response(resp)
    return resp.json()


def capture_order(order_id):
    """Take the money for an order the buyer has approved."""
    token = get_access_token()

    resp = requests.post(
        f"{config.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers=_auth_headers(token),
        timeout=TIMEOUT,
    )
    _check_response(resp)
    return resp.json()


def refund_capture(capture_id):
    """Refund a captured payment in full."""
    token = get_access_token()

    resp = requests.post(
        f"{config.PAYPAL_BASE_URL}/v2/payments/captures/{capture_id}/refund",
        headers=_auth_headers(token),
        timeout=TIMEOUT,
    )
    _check_response(resp)
    return resp.json()


def order_details(order):
    """Pull out the few fields the page needs from a PayPal order."""
    unit = (order.get("purchase_units") or [{}])[0]
    amount = unit.get("amount") or {}
    captures = (unit.get("payments") or {}).get("captures") or []
    return {
        "amount": amount.get("value"),
        "currency": amount.get("currency_code"),
        "payee": (unit.get("payee") or {}).get("email_address"),
        "custom_id": unit.get("custom_id"),
        "capture_id": captures[0].get("id") if captures else None,
    }
