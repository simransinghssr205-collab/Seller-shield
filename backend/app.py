import re

from flask import Flask, jsonify, request
from flask_cors import CORS

from . import paypal_client
from .analyzer import analyze_message

app = Flask(__name__)
CORS(app)

# order_id -> full SellerShield analysis, kept in memory for speed.
# The verdict is ALSO saved inside the PayPal order (custom_id), so it is
# still known after a restart.
ORDER_VERDICTS = {}

AMOUNT_RE = re.compile(r"^\d{1,7}(\.\d{1,2})?$")
VERDICTS = ("safe", "warning", "danger")


def _json_body():
    return request.get_json(silent=True) or {}


def _parse_amount(value):
    text = "25.00" if value in (None, "") else str(value).strip()
    if not AMOUNT_RE.match(text) or float(text) <= 0:
        raise ValueError("Enter a valid price, like 25.00")
    return f"{float(text):.2f}"


def _verdict_from_custom_id(custom_id):
    """Read 'sellershield:<verdict>:<score>' back out of a PayPal order."""
    parts = (custom_id or "").split(":")
    if len(parts) == 3 and parts[0] == "sellershield" and parts[1] in VERDICTS:
        return {
            "verdict": parts[1],
            "score": int(parts[2]) if parts[2].isdigit() else None,
            "reasons": [],
            "restored": True,
        }
    return None


@app.route("/api/paypal/test")
def paypal_test():
    try:
        paypal_client.get_access_token()
        return jsonify({"message": "PayPal Sandbox connection successful!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check-message", methods=["POST"])
def check_message_route():
    message = str(_json_body().get("message") or "").strip()
    if not message:
        return jsonify({"error": "Write or paste a buyer message first."}), 400
    return jsonify(analyze_message(message))


@app.route("/api/create-order", methods=["POST"])
def create_order_route():
    body = _json_body()
    try:
        amount = _parse_amount(body.get("amount"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        message = str(body.get("message") or "").strip()
        analysis = analyze_message(message) if message else None

        # High risk: do not even create the PayPal order.
        if analysis and analysis["verdict"] == "danger":
            reason = analysis["reasons"][0] if analysis["reasons"] else "High scam risk."
            return jsonify({
                "blocked": True,
                "error": f"SellerShield blocked this order: {reason}",
                "analysis": analysis,
            }), 403

        order = paypal_client.create_order(
            amount=amount,
            custom_id=(
                f"sellershield:{analysis['verdict']}:{analysis['score']}"
                if analysis else None
            ),
            description="Order checked by SellerShield" if analysis else None,
        )
        approve_url = next(
            (l["href"] for l in order.get("links", [])
             if l["rel"] in ("approve", "payer-action")),
            None,
        )
        if analysis:
            ORDER_VERDICTS[order["id"]] = analysis
        return jsonify({
            "id": order["id"],
            "status": order["status"],
            "approve_url": approve_url,
            "analysis": analysis,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/order/<order_id>", methods=["GET"])
def get_order_route(order_id):
    try:
        order = paypal_client.get_order(order_id)
        details = paypal_client.order_details(order)
        order["details"] = details
        order["sellershield"] = (
            ORDER_VERDICTS.get(order_id)
            or _verdict_from_custom_id(details["custom_id"])
        )
        return jsonify(order)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/order/<order_id>/capture", methods=["POST"])
def capture_order_route(order_id):
    try:
        analysis = ORDER_VERDICTS.get(order_id)
        if analysis is None:
            # After a restart, ask PayPal what verdict this order was given.
            order = paypal_client.get_order(order_id)
            analysis = _verdict_from_custom_id(
                paypal_client.order_details(order)["custom_id"]
            )

        if analysis and analysis["verdict"] == "danger":
            return jsonify({
                "blocked": True,
                "error": "SellerShield marked this order as high risk, so it will not be captured.",
                "analysis": analysis,
            }), 403

        # Suspicious: the seller must confirm before the money is taken.
        if analysis and analysis["verdict"] == "warning" and not _json_body().get("confirm"):
            return jsonify({
                "needs_confirmation": True,
                "error": "SellerShield flagged this buyer's message as suspicious. "
                         "Confirm that you want to take the payment.",
                "analysis": analysis,
            }), 409

        result = paypal_client.capture_order(order_id)
        result["capture_id"] = paypal_client.order_details(result)["capture_id"]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/capture/<capture_id>/refund", methods=["POST"])
def refund_route(capture_id):
    try:
        return jsonify(paypal_client.refund_capture(capture_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
