#!/usr/bin/env python3
"""
Quick test to verify encryption service works in MVP mode (no-op).
"""

import os
import sys

# Set MVP mode before importing
os.environ["USE_MEMORY_DB"] = "true"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.encryption_service import encrypt_field, decrypt_field, encrypt_dict_fields, decrypt_dict_fields

def test_mvp_encryption():
    """Test that encryption is no-op in MVP mode."""
    print("Testing encryption service in MVP mode...")
    print("=" * 60)
    
    # Test encrypt/decrypt field
    original = "sensitive-data-123"
    encrypted = encrypt_field(original)
    decrypted = decrypt_field(encrypted)
    
    print(f"Original:  {original}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    
    assert encrypted == original, "In MVP mode, encryption should be no-op"
    assert decrypted == original, "In MVP mode, decryption should be no-op"
    print("✓ encrypt_field/decrypt_field: PASS")
    print()
    
    # Test dict encryption
    data = {
        "name": "John Doe",
        "email": "john@example.com",
        "public_field": "not-secret"
    }
    
    encrypted_dict = encrypt_dict_fields(data, ["name", "email"])
    decrypted_dict = decrypt_dict_fields(encrypted_dict, ["name", "email"])
    
    print(f"Original dict: {data}")
    print(f"Encrypted dict: {encrypted_dict}")
    print(f"Decrypted dict: {decrypted_dict}")
    
    assert encrypted_dict["name"] == data["name"], "In MVP mode, encryption should be no-op"
    assert encrypted_dict["email"] == data["email"], "In MVP mode, encryption should be no-op"
    assert decrypted_dict == data, "Decryption should restore original"
    print("✓ encrypt_dict_fields/decrypt_dict_fields: PASS")
    print()
    
    print("=" * 60)
    print("All encryption tests passed! MVP mode working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    test_mvp_encryption()
