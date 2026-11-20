"""
extract.py
----------
Finds contact details (phone numbers, emails, websites) inside a job posting and
normalises them, so the same scammer is recognised even if they write the number
as "+91 98765 43210" in one post and "9876543210" in another.
"""
import re

# Free mail providers and big legitimate sites can never be reported (nobody should
# be able to "report gmail.com" or "linkedin.com" and make every posting look scammy).
FREE_MAIL = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com",
             "rediffmail.com", "proton.me", "protonmail.com", "icloud.com", "live.com"}
BIG_SITES = {"google.com", "linkedin.com", "naukri.com", "indeed.com", "internshala.com",
             "facebook.com", "instagram.com", "youtube.com", "whatsapp.com", "wa.me",
             "t.me", "telegram.org", "github.com", "microsoft.com", "amazon.com",
             "gov.in", "nic.in", "cybercrime.gov.in"}

TLDS = "com|in|co\\.in|net|org|xyz|info|online|site|biz|link|click|top|shop|live|store|work|jobs|app|me"
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.I)
URL_RE = re.compile(r"https?://([a-z0-9.-]+\.[a-z]{2,})", re.I)
BARE_RE = re.compile(rf"\b((?:[a-z0-9-]+\.)+(?:{TLDS}))\b", re.I)
# Indian mobile: optional +91 / 91 / 0, then 10 digits starting 6-9 (spaces or a dash allowed in the middle)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?|0)?([6-9]\d{4}[\s-]?\d{5})(?!\d)")
EMAIL_FULL = re.compile(r"[a-z0-9._%+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")
HOST_FULL = re.compile(r"(?:[a-z0-9-]+\.)+[a-z]{2,}")
MAX_ENTITIES = 10


def _is_big(host: str) -> bool:
    return any(host == b or host.endswith("." + b) for b in BIG_SITES)


def classify(raw: str):
    """Turn user input into (kind, normalised_value), or None if it is not a phone, email or website."""
    s = (raw or "").strip().lower()
    if not s or len(s) > 120:
        return None
    if EMAIL_FULL.fullmatch(s):
        return ("email", s)
    if re.fullmatch(r"[\d\s+\-()]+", s):
        digits = re.sub(r"\D", "", s)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]
        return ("phone", digits) if re.fullmatch(r"[6-9]\d{9}", digits) else None
    host = re.sub(r"^https?://", "", s).split("/")[0]
    host = host[4:] if host.startswith("www.") else host
    if HOST_FULL.fullmatch(host) and host not in FREE_MAIL and not _is_big(host):
        return ("domain", host)
    return None


def extract_entities(text: str):
    """Return a de-duplicated list of (kind, value) found in the text."""
    found = []

    def add(item):
        if item and item not in found and len(found) < MAX_ENTITIES:
            found.append(item)

    for email in EMAIL_RE.findall(text):
        add(classify(email))
        add(classify(email.split("@", 1)[1]))      # the email's domain too (None for gmail etc.)
    no_email = EMAIL_RE.sub(" ", text)
    for host in URL_RE.findall(no_email):
        add(classify(host))
    for host in BARE_RE.findall(no_email):
        add(classify(host))
    for number in PHONE_RE.findall(text):
        add(classify(number))
    return found


def mask(kind: str, value: str) -> str:
    """Public lists show partial values, so the page cannot be used to harvest numbers or emails."""
    if kind == "phone":
        return value[:2] + "XXXXX" + value[-3:]
    if kind == "email":
        name, domain = value.split("@", 1)
        return name[:1] + "***@" + domain
    return value