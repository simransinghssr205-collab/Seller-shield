"""Combines the rule checker and the AI checker into one verdict."""
from . import ai_checker, risk_rules

SEVERITY = {"safe": 0, "warning": 1, "danger": 2}
MIN_SCORE = {
    "safe": 0,
    "warning": risk_rules.WARNING_AT,
    "danger": risk_rules.DANGER_AT,
}


def analyze_message(message):
    """Always runs the rules. If an AI key is set, the AI also weighs in and
    the more severe of the two verdicts wins."""
    rules = risk_rules.check_rules(message)
    result = {
        "verdict": rules["verdict"],
        "score": rules["score"],
        "reasons": list(rules["reasons"]),
        "scam_type": rules["scam_type"],
        "suggested_reply": rules["suggested_reply"],
        "summary": None,
        "rules_verdict": rules["verdict"],
        "ai_used": False,
        "ai_verdict": None,
        "ai_error": None,
    }

    if ai_checker.ai_enabled():
        try:
            ai = ai_checker.check_with_ai(message)
        except Exception as e:  # keep working on rules alone
            result["ai_error"] = str(e)[:200]
            return result

        result["ai_used"] = True
        result["ai_verdict"] = ai["verdict"]
        result["summary"] = ai["summary"]

        if SEVERITY[ai["verdict"]] > SEVERITY[result["verdict"]]:
            result["verdict"] = ai["verdict"]
            # Keep the score in line with the verdict the AI raised it to.
            result["score"] = max(result["score"], MIN_SCORE[ai["verdict"]])

        for reason in ai["reasons"]:
            if reason not in result["reasons"]:
                result["reasons"].append(reason)

        if result["verdict"] != "safe":
            result["scam_type"] = ai["scam_type"] or result["scam_type"]
            result["suggested_reply"] = (
                ai["suggested_reply"]
                or result["suggested_reply"]
                or risk_rules.GENERIC_REPLY
            )

    if result["verdict"] == "safe":
        result["scam_type"] = None
        result["suggested_reply"] = None
    elif not result["suggested_reply"]:
        result["suggested_reply"] = risk_rules.GENERIC_REPLY

    return result
