"""
community.py
------------
Mixes the community report counts into the risk result.

Rules (kept simple on purpose, so they are easy to explain):
  * 3 or more separate reports -> "confirmed": the posting becomes at least High risk.
  * 1-2 reports               -> "warning": the posting becomes at least Suspicious.
A single report can never mark something High risk, which limits abuse.
"""
from predictor import verdict_for

CATEGORIES = {
    "fee": "Asked me for money",
    "fake": "Fake job offer",
    "id": "Asked for ID or bank details",
    "other": "Other scam",
}
CONFIRMED_AT = 3


def apply_community(result, counts):
    """counts: {(kind, value): reports}. Edits `result` in place."""
    hits = [(n, kind, value) for (kind, value), n in counts.items() if n > 0]
    if not hits:
        return
    n, kind, value = max(hits)
    times = f"{n} time" + ("" if n == 1 else "s")
    if n >= CONFIRMED_AT:
        weight, floor = 0.9, 0.7
        advice = "Other users reported this contact as a scam. Do not reply, pay or share any documents."
    else:
        weight, floor = 0.4, 0.4
        advice = "Someone reported this contact. It is not confirmed yet, so verify carefully before trusting it."
    result["red_flags"].insert(0, {
        "name": "Contact reported by the community",
        "weight": weight,
        "advice": advice,
        "matched": f"{value} (reported {times})",
    })
    result["risk_score"] = round(max(result["risk_score"], floor), 4)
    result["risk_percent"] = round(result["risk_score"] * 100)
    result["verdict"], result["level"] = verdict_for(result["risk_score"])