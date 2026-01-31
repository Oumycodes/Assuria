"""
Unit tests for PII service (redaction and pseudonymization).
"""

import pytest
from app.services.pii_service import (
    redact_pii,
    pseudonymize_pii,
    restore_pii,
    extract_pii_fields
)


def test_redact_email():
    """Test redacting email addresses."""
    text = "Contact me at john@example.com"
    redacted = redact_pii(text)
    
    assert "john@example.com" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_phone():
    """Test redacting phone numbers."""
    text = "Call me at 555-123-4567"
    redacted = redact_pii(text)
    
    assert "555-123-4567" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_ssn():
    """Test redacting SSN."""
    text = "My SSN is 123-45-6789"
    redacted = redact_pii(text)
    
    assert "123-45-6789" not in redacted
    assert "[REDACTED]" in redacted


def test_pseudonymize_pii():
    """Test pseudonymizing PII with mapping."""
    text = "Email: john@example.com, Phone: 555-123-4567"
    pseudonymized, mapping = pseudonymize_pii(text)
    
    assert "john@example.com" not in pseudonymized
    assert "555-123-4567" not in pseudonymized
    assert "[EMAIL" in pseudonymized or "[PHONE" in pseudonymized
    assert len(mapping) > 0


def test_restore_pii():
    """Test restoring PII from pseudonymized text."""
    original = "Email: john@example.com"
    pseudonymized, mapping = pseudonymize_pii(original)
    restored = restore_pii(pseudonymized, mapping)
    
    assert "john@example.com" in restored


def test_extract_pii_fields():
    """Test extracting PII fields from structured data."""
    data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567",
        "incident_type": "car_accident",
        "location": "123 Main St"
    }
    
    pii_fields = extract_pii_fields(data)
    
    assert "email" in pii_fields
    assert "phone" in pii_fields
    assert "name" in pii_fields
    assert "incident_type" not in pii_fields


def test_no_pii_in_text():
    """Test text with no PII."""
    text = "This is a normal text with no sensitive information."
    redacted = redact_pii(text)
    
    assert redacted == text


def test_multiple_emails():
    """Test redacting multiple email addresses."""
    text = "Contact john@example.com or jane@example.com"
    redacted = redact_pii(text)
    
    assert "john@example.com" not in redacted
    assert "jane@example.com" not in redacted
    assert redacted.count("[REDACTED]") >= 2
