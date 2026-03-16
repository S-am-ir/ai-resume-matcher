"""
IMAP Password Encryption Utility using Fernet (symmetric encryption).

This module provides secure encryption/decryption for Gmail IMAP passwords
stored in the database. Uses the cryptography library's Fernet implementation.

Security Notes:
- The ENCRYPTION_KEY must be stored in HF Spaces secrets (never in code)
- Same key is used for all users (simpler key management)
- If key is lost, all encrypted passwords become unrecoverable
- Users can always re-enter their password if needed
"""
from cryptography.fernet import Fernet
import os
import base64


def get_encryption_key() -> bytes:
    """
    Get the encryption key from environment variable.
    
    Returns the key as bytes, or None if not configured.
    If None, encryption is disabled and passwords are stored plaintext.
    """
    key_str = os.getenv("ENCRYPTION_KEY")
    if not key_str:
        return None
    return key_str.encode() if isinstance(key_str, str) else key_str


def is_encryption_enabled() -> bool:
    """Check if encryption is configured and available."""
    return get_encryption_key() is not None


def encrypt_password(password: str) -> str:
    """
    Encrypt an IMAP password using Fernet symmetric encryption.
    
    Args:
        password: The plaintext IMAP password to encrypt
        
    Returns:
        The encrypted password as a base64-encoded string.
        Returns the original password if encryption is not enabled.
    """
    key = get_encryption_key()
    if not key:
        # Encryption not configured, return plaintext
        # This allows backward compatibility during deployment
        return password
    
    try:
        fernet = Fernet(key)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()  # Convert bytes to string for DB storage
    except Exception as e:
        print(f"[ENCRYPTION] Error encrypting password: {e}")
        # Fallback: return plaintext (better than crashing)
        return password


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt an IMAP password.
    
    Args:
        encrypted_password: The encrypted password from the database
        
    Returns:
        The decrypted plaintext password.
        Returns the input as-is if it's not encrypted or encryption is disabled.
    """
    key = get_encryption_key()
    if not key:
        # Encryption not configured, assume stored as plaintext
        return encrypted_password
    
    try:
        fernet = Fernet(key)
        # Try to decrypt (input might already be plaintext from old records)
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        # Decryption failed - likely because password is stored as plaintext
        # (from before encryption was enabled)
        # Return as-is to maintain backward compatibility
        return encrypted_password


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Use this ONCE to create your key, then store it in HF Spaces secrets.
    Never lose this key - all encrypted passwords become unrecoverable.
    
    Returns:
        A URL-safe base64-encoded 32-byte key.
    """
    key = Fernet.generate_key()
    return key.decode()
