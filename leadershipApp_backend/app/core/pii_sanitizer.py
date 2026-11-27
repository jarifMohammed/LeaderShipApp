"""
Pre-LLM PII Sanitizer for Executive Leadership Coaching.

Scans user messages and uploaded coaching session transcripts before LLM ingestion.
Redacts and anonymizes:
1. Executive compensation and equity figures (e.g., "$450,000 base + 50k bonus", "$300k salary", "50k RSUs")
2. Personal and corporate email addresses
3. Personal phone numbers (international and national)
4. Social Security Numbers (SSN) and credit card / financial identifiers

Preserves semantic context so that coaching efficacy (e.g. negotiation strategy, equity conversations)
is completely preserved without leaking raw client PII to external model vendors or vector stores.
Supports reversible placeholder restoration when needed.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class PIICategory(str, Enum):
    COMPENSATION = "compensation"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    FINANCIAL = "financial"


class PIIRedaction(BaseModel):
    category: PIICategory
    placeholder: str
    original_value: str
    start: int
    end: int


class SanitizationResult(BaseModel):
    sanitized_text: str
    has_pii: bool
    redactions: List[PIIRedaction] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "has_pii": self.has_pii,
            "total_redactions": len(self.redactions),
            "counts": self.counts,
        }


class PIISanitizer:
    # -------------------------------------------------------------------------
    # 1. Regex Patterns
    # -------------------------------------------------------------------------

    # Email: standard RFC 5322 pattern
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        re.IGNORECASE,
    )

    # SSN: 123-45-6789
    SSN_PATTERN = re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    )

    # Financial / Credit Card numbers: 16 digits (grouped by 4s with optional hyphens/spaces)
    CREDIT_CARD_PATTERN = re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    )

    # Phone numbers: US and international patterns with area codes, extensions, or country codes
    # Guard against 4-digit years or zip codes with strict structural anchors
    PHONE_PATTERNS = [
        # +1 (555) 234-5678, +44 20 7946 0950, +49 30 123456
        re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        # International with country code: +44 1234 567890
        re.compile(r"\+\d{1,3}(?:[-.\s]?\d{2,4}){2,4}\b"),
    ]

    # Executive Compensation & Equity Patterns:
    # Handles:
    # - "$450,000 base + 50k bonus"
    # - "$350,000 base salary", "$350k base"
    # - "base salary of $250,000"
    # - "$1.5M equity", "50,000 RSUs", "25,000 stock options"
    # - "$200k bonus", "15% annual bonus" (in compensation context)
    # - "EUR 180,000 package", "£150,000 salary"
    COMPENSATION_PATTERNS = [
        # Multi-component compensation: "$450,000 base + 50k bonus", "$350k base + 20% bonus + 500k RSUs"
        re.compile(
            r"[\$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b|K|M|B)?\s+(?:base|salary|comp|compensation)"
            r"(?:\s*(?:\+|\band\b)\s*[\$€£]?\s?\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b|K|M|B)?\s*(?:bonus|equity|rsus?|options?|stocks?|target)?)*",
            re.IGNORECASE,
        ),
        # Dollar/currency figure directly followed by compensation terminology
        re.compile(
            r"[\$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b|K|M|B)?\s*(?:base(?:\s+salary)?|salary|annual\s+bonus|sign-?on\s+bonus|equity|rsus?|stock\s+options?|total\s+comp(?:ensation)?|package)\b",
            re.IGNORECASE,
        ),
        # Terminology followed by currency figure: "base salary of $350,000", "salary of 200k USD", "package of £180k"
        re.compile(
            r"\b(?:base(?:\s+salary)?|salary|total\s+comp(?:ensation)?|compensation|package|bonus|equity)\s+(?:of|is|at|around)?\s*[\$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b|K|M|B)?\b",
            re.IGNORECASE,
        ),
        # RSUs and stock options with quantities: "50,000 RSUs", "25k stock options", "100k equity grant"
        re.compile(
            r"\b\d+(?:,\d{3})*(?:k|m|K|M)?\s+(?:rsus?|stock\s+options?|equity\s+grant|shares)\b",
            re.IGNORECASE,
        ),
        # Explicit numbers with currency code: "450,000 USD salary", "180,000 EUR base"
        re.compile(
            r"\b\d+(?:,\d{3})*(?:k|m|K|M)?\s+(?:USD|EUR|GBP|CAD|AUD)\s+(?:base|salary|bonus|package|comp|compensation)\b",
            re.IGNORECASE,
        ),
    ]

    # Standard placeholders
    PLACEHOLDERS = {
        PIICategory.COMPENSATION: "[CONFIDENTIAL_COMPENSATION]",
        PIICategory.EMAIL: "[CONFIDENTIAL_EMAIL]",
        PIICategory.PHONE: "[CONFIDENTIAL_PHONE]",
        PIICategory.SSN: "[CONFIDENTIAL_SSN]",
        PIICategory.FINANCIAL: "[CONFIDENTIAL_FINANCIAL_ID]",
    }

    @classmethod
    def sanitize(
        cls,
        text: str,
        reversible: bool = False,
    ) -> SanitizationResult:
        """
        Scans and sanitizes PII from the input string.
        Returns SanitizationResult with redacted text and metadata.
        If reversible is True, placeholders are indexed (e.g., [CONFIDENTIAL_EMAIL_1])
        to allow exact round-trip unmasking via `restore()`.
        """
        if not text:
            return SanitizationResult(sanitized_text="", has_pii=False)

        redactions: List[PIIRedaction] = []
        category_counters: Dict[str, int] = {cat.value: 0 for cat in PIICategory}

        # 1. Detect Compensation (run first before emails/phones to capture composite expressions)
        for pattern in cls.COMPENSATION_PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(0).strip()
                category_counters[PIICategory.COMPENSATION.value] += 1
                idx = category_counters[PIICategory.COMPENSATION.value]
                ph = (
                    f"[CONFIDENTIAL_COMPENSATION_{idx}]"
                    if reversible
                    else cls.PLACEHOLDERS[PIICategory.COMPENSATION]
                )
                redactions.append(
                    PIIRedaction(
                        category=PIICategory.COMPENSATION,
                        placeholder=ph,
                        original_value=val,
                        start=match.start(),
                        end=match.end(),
                    )
                )

        # 2. Detect Emails
        for match in cls.EMAIL_PATTERN.finditer(text):
            val = match.group(0).strip()
            # Avoid overlaps with previously matched spans
            if any(r.start <= match.start() and r.end >= match.end() for r in redactions):
                continue
            category_counters[PIICategory.EMAIL.value] += 1
            idx = category_counters[PIICategory.EMAIL.value]
            ph = (
                f"[CONFIDENTIAL_EMAIL_{idx}]"
                if reversible
                else cls.PLACEHOLDERS[PIICategory.EMAIL]
            )
            redactions.append(
                PIIRedaction(
                    category=PIICategory.EMAIL,
                    placeholder=ph,
                    original_value=val,
                    start=match.start(),
                    end=match.end(),
                )
            )

        # 3. Detect SSN
        for match in cls.SSN_PATTERN.finditer(text):
            val = match.group(0).strip()
            if any(r.start <= match.start() and r.end >= match.end() for r in redactions):
                continue
            category_counters[PIICategory.SSN.value] += 1
            idx = category_counters[PIICategory.SSN.value]
            ph = (
                f"[CONFIDENTIAL_SSN_{idx}]"
                if reversible
                else cls.PLACEHOLDERS[PIICategory.SSN]
            )
            redactions.append(
                PIIRedaction(
                    category=PIICategory.SSN,
                    placeholder=ph,
                    original_value=val,
                    start=match.start(),
                    end=match.end(),
                )
            )

        # 4. Detect Credit Cards
        for match in cls.CREDIT_CARD_PATTERN.finditer(text):
            val = match.group(0).strip()
            if any(r.start <= match.start() and r.end >= match.end() for r in redactions):
                continue
            category_counters[PIICategory.FINANCIAL.value] += 1
            idx = category_counters[PIICategory.FINANCIAL.value]
            ph = (
                f"[CONFIDENTIAL_FINANCIAL_{idx}]"
                if reversible
                else cls.PLACEHOLDERS[PIICategory.FINANCIAL]
            )
            redactions.append(
                PIIRedaction(
                    category=PIICategory.FINANCIAL,
                    placeholder=ph,
                    original_value=val,
                    start=match.start(),
                    end=match.end(),
                )
            )

        # 5. Detect Phone Numbers
        for phone_pat in cls.PHONE_PATTERNS:
            for match in phone_pat.finditer(text):
                val = match.group(0).strip()
                # Check for overlap
                if any(r.start <= match.start() and r.end >= match.end() for r in redactions):
                    continue
                # Simple sanity check: must contain at least 7 digits
                digits = re.sub(r"\D", "", val)
                if len(digits) < 7:
                    continue
                category_counters[PIICategory.PHONE.value] += 1
                idx = category_counters[PIICategory.PHONE.value]
                ph = (
                    f"[CONFIDENTIAL_PHONE_{idx}]"
                    if reversible
                    else cls.PLACEHOLDERS[PIICategory.PHONE]
                )
                redactions.append(
                    PIIRedaction(
                        category=PIICategory.PHONE,
                        placeholder=ph,
                        original_value=val,
                        start=match.start(),
                        end=match.end(),
                    )
                )

        if not redactions:
            return SanitizationResult(
                sanitized_text=text,
                has_pii=False,
                redactions=[],
                counts={k: v for k, v in category_counters.items() if v > 0},
            )

        # Sort redactions from end of text to beginning so indices remain stable during replacement
        # Also deduplicate overlapping spans by picking the longest span
        redactions = cls._resolve_overlaps(redactions)
        redactions.sort(key=lambda r: r.start, reverse=True)

        sanitized = text
        for red in redactions:
            sanitized = sanitized[:red.start] + red.placeholder + sanitized[red.end:]

        # Sort back to reading order
        redactions.sort(key=lambda r: r.start)

        active_counts = {k: v for k, v in category_counters.items() if v > 0}

        return SanitizationResult(
            sanitized_text=sanitized,
            has_pii=True,
            redactions=redactions,
            counts=active_counts,
        )

    @classmethod
    def restore(cls, sanitized_text: str, redactions: List[PIIRedaction]) -> str:
        """
        Reverses the sanitization by mapping placeholders back to original values.
        """
        if not sanitized_text or not redactions:
            return sanitized_text

        restored = sanitized_text
        for r in redactions:
            if r.placeholder in restored:
                restored = restored.replace(r.placeholder, r.original_value, 1)

        return restored

    @staticmethod
    def _resolve_overlaps(redactions: List[PIIRedaction]) -> List[PIIRedaction]:
        """Resolves overlapping redaction spans by keeping the longer match."""
        if not redactions:
            return []

        # Sort by start asc, then length desc
        sorted_reds = sorted(
            redactions,
            key=lambda r: (r.start, -(r.end - r.start)),
        )

        resolved: List[PIIRedaction] = []
        last_end = -1

        for r in sorted_reds:
            if r.start >= last_end:
                resolved.append(r)
                last_end = r.end
            else:
                # Overlap: keep the longer span if it extends further
                if resolved and (r.end - r.start) > (resolved[-1].end - resolved[-1].start):
                    resolved[-1] = r
                    last_end = r.end

        return resolved

