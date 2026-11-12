"""Rule-based scam checks for buyer messages. Works with no API key."""
import re

# (key, pattern, weight, reason shown to the seller)
RULES = [
    (
        "overpayment",
        r"overpa(?:id|y|yment)"
        r"|send (?:me |it )?back the (?:difference|extra|balance|rest)"
        r"|refund (?:me )?the (?:difference|extra|balance)"
        r"|pay(?:ing)? (?:you )?extra"
        r"|extra (?:money|amount|payment)"
        r"|keep your fee"
        r"|send the (?:rest|balance|difference) (?:back|to)",
        50,
        "Overpayment trick: asks you to send money back to them",
    ),
    (
        "off_platform_payment",
        r"western union|moneygram|gift ?cards?|zelle|cash ?app|wire transfer"
        r"|bank transfer|bitcoin|crypto(?:currency)?|usdt"
        r"|friends (?:and|&) family|outside (?:of )?paypal",
        40,
        "Wants to pay or be paid outside PayPal's protection",
    ),
    (
        "shipping_agent",
        r"shipping agent|freight forwarder|(?:my|our) (?:courier|agent|forwarder)"
        r"|(?:agent|courier) will (?:pick|collect)",
        35,
        "A third-party agent or courier will collect the item",
    ),
    (
        "sensitive_info",
        r"password|\botp\b|verification code|security code|\bcvv\b"
        r"|card number|\bpin\b|login details",
        60,
        "Asks for a password, a code or card details",
    ),
    (
        "phishing_link",
        r"https?://|www\.|bit\.ly|tinyurl|click (?:the |this |on )?(?:link|here)"
        r"|verify your account|log ?in to (?:confirm|release|verify)",
        30,
        "Contains a link or asks you to log in somewhere",
    ),
    (
        "fake_payment_claim",
        r"already (?:sent|paid|made)"
        r"|payment (?:has been |was |is )?(?:sent|made|done|pending)"
        r"|i(?:'ve| have) (?:paid|sent the payment)"
        r"|check your email for the receipt"
        r"|funds (?:are )?(?:pending|on hold)",
        25,
        "Claims the payment was sent or is pending, so you ship before it clears",
    ),
    (
        "off_platform_contact",
        r"whatsapp|telegram|text me|call me|email me|@gmail|@yahoo|@outlook"
        r"|my number is",
        25,
        "Wants to move the conversation off the platform",
    ),
    (
        "urgency",
        r"urgent|immediately|asap|right away|within the hour|today only"
        r"|last chance|hurry|act now",
        15,
        "Puts pressure on you to act quickly",
    ),
]

SCAM_NAMES = {
    "overpayment": "Overpayment scam",
    "off_platform_payment": "Payment outside PayPal",
    "shipping_agent": "Fake shipping agent",
    "sensitive_info": "Phishing for passwords or codes",
    "phishing_link": "Phishing link",
    "fake_payment_claim": "Fake payment claim",
    "off_platform_contact": "Moving off the platform",
    "urgency": "Pressure tactics",
}

# Safe replies a seller can send back. Used when the AI is off or gives none.
REPLIES = {
    "overpayment": (
        "Thanks for your interest. I can only accept the exact listed price through "
        "PayPal checkout, and I don't send back change or refund extra payments. "
        "If you'd like to buy, please pay the listed price."
    ),
    "off_platform_payment": (
        "Thanks for your interest. I only accept payment through PayPal checkout, "
        "so I can't use any other payment method."
    ),
    "shipping_agent": (
        "Thanks for your interest. I only ship to the buyer's own address shown on "
        "the PayPal order, not to a third-party agent or courier."
    ),
    "sensitive_info": (
        "I never share passwords, codes or card details, and no genuine buyer "
        "should ask for them. I'm ending this conversation."
    ),
    "phishing_link": (
        "I don't open links or log in to other sites to confirm payments. "
        "I'll only ship once the payment shows as completed in my own PayPal account."
    ),
    "fake_payment_claim": (
        "I'll ship once the payment shows as completed in my own PayPal account. "
        "A receipt or an email isn't enough for me."
    ),
    "off_platform_contact": (
        "I'd like to keep all messages here so we are both protected. "
        "Please send any questions in this chat."
    ),
    "urgency": (
        "Happy to help, but I don't rush orders. I'll ship once the payment shows "
        "as completed in my PayPal account."
    ),
}

GENERIC_REPLY = (
    "Thanks for your message. I only accept payment through PayPal checkout at the "
    "listed price, and I ship once the payment shows as completed in my own account."
)

_COMPILED = [
    (key, re.compile(pattern, re.IGNORECASE), weight, reason)
    for key, pattern, weight, reason in RULES
]
WEIGHTS = {key: weight for key, _, weight, _ in RULES}

DANGER_AT = 60
WARNING_AT = 25


def verdict_for(score):
    if score >= DANGER_AT:
        return "danger"
    if score >= WARNING_AT:
        return "warning"
    return "safe"


def check_rules(message):
    """Return verdict, score, reasons, matched rule keys, scam type and a reply."""
    text = (message or "").strip()
    score = 0
    reasons = []
    matched = []
    for key, pattern, weight, reason in _COMPILED:
        if pattern.search(text):
            score += weight
            reasons.append(reason)
            matched.append(key)
    score = min(score, 100)
    verdict = verdict_for(score)

    top = max(matched, key=lambda k: WEIGHTS[k]) if matched else None
    flagged = top is not None and verdict != "safe"
    return {
        "verdict": verdict,
        "score": score,
        "reasons": reasons,
        "matched": matched,
        "scam_type": SCAM_NAMES[top] if flagged else None,
        "suggested_reply": REPLIES[top] if flagged else None,
    }
