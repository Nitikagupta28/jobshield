"""
rules.py
--------
A small rule engine that spots well-known scam patterns using regular expressions.

Why add rules when we have ML?
  * ML learns patterns from data, but it can miss brand-new tricks.
  * Rules are fully explainable ("you asked for a fee") and work even for rare cases.
Combining both (a "hybrid" system) is common in real fraud detection.
"""
import re
from dataclasses import dataclass


@dataclass
class Rule:
    name: str          # short label shown in the UI
    pattern: str       # regex searched in the posting text
    weight: float      # how serious this flag is (0 to 1)
    advice: str        # plain-language explanation for the user


RULES = [
    Rule("Asks for money", r"(registration|processing|security|training|joining|refundable)\s+(fee|deposit|charges?)|pay\s+(a\s+)?(small\s+)?(fee|amount|deposit)|deposit\s+for",
         0.9, "Real employers never charge candidates. Any fee to get a job is a scam."),
    Rule("Wants sensitive documents early", r"aadhaar|aadhar|\bpan\b|bank account (details|number)|otp|passport copy|card number",
         0.8, "Never share ID or bank details before a verified offer letter and official onboarding."),
    Rule("Chat-app only contact", r"whatsapp|telegram|signal app",
         0.5, "Genuine companies hire through official email, portals and video or in-person interviews."),
    Rule("Personal email domain", r"[\w.+-]+@(gmail|yahoo|outlook|hotmail|rediffmail)\.\w+",
         0.5, "Official recruiters use a company email domain, not a free personal email."),
    Rule("Unrealistic earnings", r"(earn|make)\s+(rs\.?|inr|₹)?\s*\d{4,}|lakhs?\s+(from|per)|unlimited\s+(earning|income|money)|guaranteed\s+(income|salary|earning|bonus)",
         0.7, "Promises of huge guaranteed income for easy work are a classic scam sign."),
    Rule("No interview / no experience", r"no\s+interview|without\s+(an\s+)?interview|direct\s+joining|no\s+experience\s+(needed|required)|anyone\s+can\s+apply",
         0.5, "Real jobs have a selection process and some requirements."),
    Rule("Pressure and urgency", r"hurry|limited\s+(seats|vacanc)|apply\s+immediately|only\s+few\s+(seats|vacanc)|urgent\s+requirement|!{3,}",
         0.4, "Scammers rush you so you do not think or verify."),
    Rule("Too-easy work", r"copy\s*paste|simple\s+typing|ad\s+posting|forward\s+(our\s+)?messages|work\s+only\s+\d+\s+hours?",
         0.4, "Simple tasks for high pay is a typical bait. Be careful."),
]


def run_rules(text: str):
    """Return (list of triggered flags, overall rule score between 0 and 1)."""
    text = (text or "").lower()
    flags = []
    for rule in RULES:
        match = re.search(rule.pattern, text)
        if match:
            flags.append({
                "name": rule.name,
                "weight": rule.weight,
                "advice": rule.advice,
                "matched": match.group(0).strip()[:60],
            })

    # Combine weights so several flags raise the score, but it never exceeds 1.
    # score = 1 - product(1 - weight)  (like "probability at least one is a real scam signal")
    remaining = 1.0
    for f in flags:
        remaining *= (1 - f["weight"])
    score = round(1 - remaining, 4)
    return flags, score
