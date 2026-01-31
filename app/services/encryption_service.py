"""
Field-level encryption service using Fernet (symmetric encryption).
Encrypts PII before storage, decrypts when needed.
For MVP mode, uses no-op encryption (returns data unchanged).
"""

from app.config import settings
import base64
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Check if we're in MVP mode
_use_mvp_encryption = settings.use_memory_db

# Initialize Fernet cipher only if not in MVP mode
_fernet = None
if not _use_mvp_encryption:
    try:
        from cryptography.fernet import Fernet
        _fernet = Fernet(settings.encryption_key.encode())
        logger.info("Fernet encryption initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Fernet encryption, using MVP mode: {e}")
        _use_mvp_encryption = True

if _use_mvp_encryption:
    logger.info("Using no-op encryption (MVP mode)")


def encrypt_field(value: str) -> str:
    """
    Encrypt a string field (PII) before storage.
    In MVP mode, returns value unchanged (no-op).
    
    Args:
        value: Plain text string to encrypt
        
    Returns:
        Encrypted string (or unchanged in MVP mode)
    """
    if not value:
        return value
    
    # MVP mode: no-op encryption
    if _use_mvp_encryption or _fernet is None:
        return value
    
    try:
        encrypted = _fernet.encrypt(value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt a field after retrieval from database.
    In MVP mode, returns value unchanged (no-op).
    
    Args:
        encrypted_value: Base64-encoded encrypted string (or plain text in MVP mode)
        
    Returns:
        Decrypted plain text string (or unchanged in MVP mode)
    """
    if not encrypted_value:
        return encrypted_value
    
    # MVP mode: no-op decryption
    if _use_mvp_encryption or _fernet is None:
        return encrypted_value
    
    try:
        encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
        decrypted = _fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise


def encrypt_dict_fields(data: Dict[str, Any], fields_to_encrypt: list[str]) -> Dict[str, Any]:
    """
    Encrypt specified fields in a dictionary.
    
    Args:
        data: Dictionary containing fields to encrypt
        fields_to_encrypt: List of field names to encrypt
        
    Returns:
        Dictionary with specified fields encrypted
    """
    encrypted_data = data.copy()
    
    for field in fields_to_encrypt:
        if field in encrypted_data and isinstance(encrypted_data[field], str):
            encrypted_data[field] = encrypt_field(encrypted_data[field])
    
    return encrypted_data


def decrypt_dict_fields(data: Dict[str, Any], fields_to_decrypt: list[str]) -> Dict[str, Any]:
    """
    Decrypt specified fields in a dictionary.
    
    Args:
        data: Dictionary containing encrypted fields
        fields_to_decrypt: List of field names to decrypt
        
    Returns:
        Dictionary with specified fields decrypted
    """
    decrypted_data = data.copy()
    
    for field in fields_to_decrypt:
        if field in decrypted_data and isinstance(decrypted_data[field], str):
            decrypted_data[field] = decrypt_field(decrypted_data[field])
    
    return decrypted_data
