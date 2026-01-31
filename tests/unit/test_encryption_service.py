"""
Unit tests for encryption service.
"""

import pytest
from app.services.encryption_service import (
    encrypt_field,
    decrypt_field,
    encrypt_dict_fields,
    decrypt_dict_fields
)


def test_encrypt_decrypt_field():
    """Test encrypting and decrypting a single field."""
    original = "sensitive-data-123"
    encrypted = encrypt_field(original)
    
    assert encrypted != original
    assert len(encrypted) > len(original)
    
    decrypted = decrypt_field(encrypted)
    assert decrypted == original


def test_encrypt_empty_field():
    """Test encrypting empty string."""
    result = encrypt_field("")
    assert result == ""


def test_encrypt_dict_fields():
    """Test encrypting multiple fields in a dictionary."""
    data = {
        "name": "John Doe",
        "email": "john@example.com",
        "public_field": "not-secret"
    }
    
    fields_to_encrypt = ["name", "email"]
    encrypted = encrypt_dict_fields(data, fields_to_encrypt)
    
    assert encrypted["name"] != data["name"]
    assert encrypted["email"] != data["email"]
    assert encrypted["public_field"] == data["public_field"]
    
    # Decrypt
    decrypted = decrypt_dict_fields(encrypted, fields_to_encrypt)
    assert decrypted["name"] == data["name"]
    assert decrypted["email"] == data["email"]


def test_encrypt_nonexistent_field():
    """Test encrypting fields that don't exist."""
    data = {"field1": "value1"}
    encrypted = encrypt_dict_fields(data, ["nonexistent"])
    assert encrypted == data


def test_encrypt_non_string_field():
    """Test that non-string fields are skipped."""
    data = {
        "string_field": "value",
        "int_field": 123,
        "dict_field": {"nested": "value"}
    }
    
    encrypted = encrypt_dict_fields(data, ["string_field", "int_field", "dict_field"])
    assert encrypted["string_field"] != data["string_field"]
    assert encrypted["int_field"] == data["int_field"]  # Not encrypted
    assert encrypted["dict_field"] == data["dict_field"]  # Not encrypted
