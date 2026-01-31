"""
PII (Personally Identifiable Information) redaction and pseudonymization.
Removes or replaces PII before sending to LLM for processing.
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Common PII patterns
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

# Pseudonymization mapping (stores original -> pseudonym)
_pseudonym_map: Dict[str, str] = {}


def redact_pii(text: str, redaction_char: str = "[REDACTED]") -> str:
    """
    Redact PII from text by replacing with placeholder.
    
    Args:
        text: Input text containing potential PII
        redaction_char: String to replace PII with
        
    Returns:
        Text with PII redacted
    """
    redacted_text = text
    
    for pii_type, pattern in PII_PATTERNS.items():
        redacted_text = re.sub(pattern, redaction_char, redacted_text, flags=re.IGNORECASE)
    
    return redacted_text


def pseudonymize_pii(text: str) -> tuple[str, Dict[str, str]]:
    """
    Replace PII with pseudonyms (reversible mapping).
    Returns both pseudonymized text and mapping for later restoration.
    
    Args:
        text: Input text containing PII
        
    Returns:
        Tuple of (pseudonymized_text, mapping_dict)
    """
    pseudonymized_text = text
    mapping: Dict[str, str] = {}
    counter = 1
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        
        for match in matches:
            original = match.group(0)
            
            if original not in mapping:
                # Generate pseudonym
                pseudonym = f"[{pii_type.upper()}_{counter}]"
                mapping[original] = pseudonym
                counter += 1
            
            pseudonym = mapping[original]
            pseudonymized_text = pseudonymized_text.replace(original, pseudonym, 1)
    
    return pseudonymized_text, mapping


def restore_pii(text: str, mapping: Dict[str, str]) -> str:
    """
    Restore original PII from pseudonymized text using mapping.
    
    Args:
        text: Pseudonymized text
        mapping: Dictionary mapping pseudonyms to original values
        
    Returns:
        Text with PII restored
    """
    restored_text = text
    
    # Reverse mapping: pseudonym -> original
    reverse_mapping = {v: k for k, v in mapping.items()}
    
    for pseudonym, original in reverse_mapping.items():
        restored_text = restored_text.replace(pseudonym, original)
    
    return restored_text


def extract_pii_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and identify PII fields from structured data.
    Used for selective encryption.
    
    Args:
        data: Dictionary potentially containing PII
        
    Returns:
        Dictionary with PII fields identified
    """
    pii_fields = {}
    
    # Common PII field names
    pii_field_names = [
        'email', 'phone', 'phone_number', 'ssn', 'social_security',
        'address', 'name', 'first_name', 'last_name', 'full_name',
        'date_of_birth', 'dob', 'license_number', 'policy_number',
        'credit_card', 'account_number'
    ]
    
    for key, value in data.items():
        key_lower = key.lower()
        if any(pii_name in key_lower for pii_name in pii_field_names):
            if isinstance(value, str) and value:
                pii_fields[key] = value
    
    return pii_fields
