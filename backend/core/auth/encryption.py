"""Encryption utilities for sensitive data like API keys."""
import os
import base64
from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from environment.
    
    Returns:
        Fernet-compatible encryption key
    """
    key = os.getenv("ENCRYPTION_KEY")
    
    if not key:
        # Generate a new key if not found (for development)
        # In production, this should be set in environment variables
        key = Fernet.generate_key().decode()
        print(f"WARNING: No ENCRYPTION_KEY found. Generated new key: {key}")
        print("Please add this to your .env file!")
    
    # Convert string key to bytes if needed
    if isinstance(key, str):
        key = key.encode()
    
    return key


def encrypt_data(plaintext: str) -> str:
    """
    Encrypt sensitive data.
    
    Args:
        plaintext: Data to encrypt
        
    Returns:
        Base64-encoded encrypted data
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_data(ciphertext: str) -> str:
    """
    Decrypt sensitive data.
    
    Args:
        ciphertext: Base64-encoded encrypted data
        
    Returns:
        Decrypted plaintext
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(ciphertext.encode())
    return decrypted.decode()
