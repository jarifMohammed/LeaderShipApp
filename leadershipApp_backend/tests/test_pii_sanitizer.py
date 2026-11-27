import unittest
from app.core.pii_sanitizer import PIICategory, PIISanitizer


class TestPIISanitizer(unittest.TestCase):
    def test_executive_compensation_sanitization(self):
        """Verify executive compensation, bonus, and equity figures are properly sanitized."""
        samples = [
            (
                "My current package is $450,000 base + 50k bonus.",
                "My current package is [CONFIDENTIAL_COMPENSATION].",
            ),
            (
                "I was offered $350k base and 50,000 RSUs by the board.",
                "I was offered [CONFIDENTIAL_COMPENSATION] and [CONFIDENTIAL_COMPENSATION] by the board.",
            ),
            (
                "My base salary of $250,000 feels below market.",
                "My [CONFIDENTIAL_COMPENSATION] feels below market.",
            ),
            (
                "They offered me a total comp of $600k with $1.5M equity grant.",
                "They offered me a [CONFIDENTIAL_COMPENSATION] with [CONFIDENTIAL_COMPENSATION].",
            ),
            (
                "In Europe, my offer was 180,000 EUR base salary.",
                "In Europe, my offer was [CONFIDENTIAL_COMPENSATION].",
            ),
        ]

        for text, expected in samples:
            result = PIISanitizer.sanitize(text)
            self.assertTrue(result.has_pii, f"Failed to detect PII in: {text}")
            self.assertIn("compensation", result.counts)
            self.assertNotIn("$450,000", result.sanitized_text)
            self.assertNotIn("50,000 RSUs", result.sanitized_text)
            self.assertNotIn("$250,000", result.sanitized_text)

    def test_email_sanitization(self):
        """Verify personal and corporate emails are anonymized."""
        text = "Please reach out to me at alex.smith@leadershipcorp.com or ceo@acme.org."
        result = PIISanitizer.sanitize(text)
        self.assertTrue(result.has_pii)
        self.assertEqual(result.counts.get("email"), 2)
        self.assertNotIn("alex.smith@leadershipcorp.com", result.sanitized_text)
        self.assertNotIn("ceo@acme.org", result.sanitized_text)
        self.assertIn("[CONFIDENTIAL_EMAIL]", result.sanitized_text)

    def test_phone_number_sanitization(self):
        """Verify telephone numbers are anonymized."""
        samples = [
            "You can call my mobile at +1 (555) 234-5678 regarding this decision.",
            "My London office number is +44 20 7946 0950.",
            "Direct line: 555-987-6543.",
        ]

        for text in samples:
            result = PIISanitizer.sanitize(text)
            self.assertTrue(result.has_pii)
            self.assertIn("phone", result.counts)
            self.assertIn("[CONFIDENTIAL_PHONE]", result.sanitized_text)

    def test_government_and_financial_ids(self):
        """Verify SSN and credit card numbers are anonymized."""
        text = "SSN: 123-45-6789 and card 4111-2222-3333-4444 should never be sent to the LLM."
        result = PIISanitizer.sanitize(text)
        self.assertTrue(result.has_pii)
        self.assertNotIn("123-45-6789", result.sanitized_text)
        self.assertNotIn("4111-2222-3333-4444", result.sanitized_text)
        self.assertIn("[CONFIDENTIAL_SSN]", result.sanitized_text)
        self.assertIn("[CONFIDENTIAL_FINANCIAL_ID]", result.sanitized_text)

    def test_preserves_non_pii_leadership_context(self):
        """Verify standard leadership, organizational metrics, and conversational text are NOT falsely redacted."""
        clean_samples = [
            "I manage a team of 15 senior staff engineers across 3 time zones.",
            "In Q3 2025, our goal is to improve team retention by 25%.",
            "I've been in this VP role for 6 years and need help delegating.",
            "My 1-on-1 with the CEO went well, but we disagree on the 2026 product roadmap.",
            "We had 3 incidents last week and 10 customer escalations.",
        ]

        for text in clean_samples:
            result = PIISanitizer.sanitize(text)
            self.assertFalse(result.has_pii, f"False positive PII detection on: {text}")
            self.assertEqual(result.sanitized_text, text)
            self.assertEqual(len(result.redactions), 0)

    def test_reversible_sanitization_and_restoration(self):
        """Verify reversible mode can restore original text when needed."""
        text = "Offer: $350k base + 20% bonus at contact@acme.com. Phone: 555-123-4567."
        result = PIISanitizer.sanitize(text, reversible=True)
        self.assertTrue(result.has_pii)
        self.assertIn("[CONFIDENTIAL_COMPENSATION_1]", result.sanitized_text)
        self.assertIn("[CONFIDENTIAL_EMAIL_1]", result.sanitized_text)
        self.assertIn("[CONFIDENTIAL_PHONE_1]", result.sanitized_text)

        restored = PIISanitizer.restore(result.sanitized_text, result.redactions)
        self.assertEqual(restored, text)

    def test_empty_and_whitespace_handling(self):
        """Verify empty and whitespace strings return safe empty results."""
        self.assertFalse(PIISanitizer.sanitize("").has_pii)
        self.assertFalse(PIISanitizer.sanitize(None).has_pii)


if __name__ == "__main__":
    unittest.main()

