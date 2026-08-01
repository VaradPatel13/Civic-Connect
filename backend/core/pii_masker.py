"""PII Masking and Security Utilities for CivicConnect AI Pipeline.

Masks citizen PII (phone numbers, email addresses, Aadhaar/IDs, credit cards)
before text is transmitted to external AI providers or logged.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import re

# Regex patterns for citizen PII
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b|(?:\+91[\-\s]?)?[6-9]\d{9}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.IGNORECASE)
AADHAAR_REGEX = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Masks citizen PII from input text before external model processing.

    Returns:
        (sanitised_text, masked_flags)
    """
    if not text:
        return "", []

    masked_flags: list[str] = []
    sanitised = text

    if PHONE_REGEX.search(sanitised):
        sanitised = PHONE_REGEX.sub("[PHONE_MASKED]", sanitised)
        masked_flags.append("phone_masked")

    if EMAIL_REGEX.search(sanitised):
        sanitised = EMAIL_REGEX.sub("[EMAIL_MASKED]", sanitised)
        masked_flags.append("email_masked")

    if AADHAAR_REGEX.search(sanitised):
        sanitised = AADHAAR_REGEX.sub("[ID_MASKED]", sanitised)
        masked_flags.append("aadhaar_masked")

    if CREDIT_CARD_REGEX.search(sanitised):
        sanitised = CREDIT_CARD_REGEX.sub("[CARD_MASKED]", sanitised)
        masked_flags.append("card_masked")

    return sanitised, masked_flags
