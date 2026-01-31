#!/usr/bin/env python3
"""
Utility script to generate a Fernet encryption key for PII encryption.
Run this and add the output to your .env file as ENCRYPTION_KEY.
"""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print(f"\nGenerated encryption key:")
    print(f"ENCRYPTION_KEY={key.decode()}\n")
    print("Add this to your .env file.\n")
