from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Any

# Order matters: more-specific patterns run first so a 12-digit CCCD does not
# swallow the middle of a 16-digit credit card, etc.
PII_PATTERNS: dict[str, str] = {
    "credit_card": r"\b(?:\d[ -]?){13,19}\b",
    "jwt": r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
    "api_key": r"\b(?:sk|pk|rk|xoxb|ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_-]{16,}\b",
    "email": r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
    "phone_vn": r"(?<!\d)(?:\+?84|0)[ .\-]?\d{2,3}[ .\-]?\d{3}[ .\-]?\d{3,4}(?!\d)",
    "passport": r"\b[A-Z]\d{7,8}\b",
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "address_vn": r"(?i)\b(?:số nhà|đường|phường|quận|thành phố|tp\.?|hcm|hà nội)\b[^,\n]{0,60}",
}

_COMPILED: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile(pat)) for name, pat in PII_PATTERNS.items()
]

# Avoid re-scrubbing already-redacted markers on subsequent passes.
_REDACTED_MARKER = re.compile(r"\[REDACTED_[A-Z_]+\]")


def scrub_text(text: Any) -> Any:
    """Redact PII from a string. Non-string inputs are returned unchanged."""
    if not isinstance(text, str) or not text:
        return text
    # Short-circuit if the whole string is already a redaction marker.
    if _REDACTED_MARKER.fullmatch(text):
        return text
    safe = text
    for name, pattern in _COMPILED:
        safe = pattern.sub(f"[REDACTED_{name.upper()}]", safe)
    return safe


def scrub_value(value: Any) -> Any:
    """Recursively scrub strings inside dicts, lists, tuples, and sets."""
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, dict):
        return {k: scrub_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(scrub_value(v) for v in value)
    if isinstance(value, set):
        return {scrub_value(v) for v in value}
    return value


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    """HMAC-SHA256 with an env-provided salt so hashes are not trivially reversible.

    Falls back to a plain digest if ``USER_ID_SALT`` is not set, matching the
    earlier behaviour for tests and local dev.
    """
    salt = os.getenv("USER_ID_SALT", "")
    raw = user_id.encode("utf-8")
    if salt:
        digest = hmac.new(salt.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    else:
        digest = hashlib.sha256(raw).hexdigest()
    return digest[:12]
