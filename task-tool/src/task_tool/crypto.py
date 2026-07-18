"""Fernet encryption/decryption for snapshot data."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


def generate_fernet_key() -> str:
    """Generate a new Fernet key and return it as a base64 string."""
    return Fernet.generate_key().decode()


def encrypt(data: bytes, key: str) -> bytes:
    """Encrypt data with the given Fernet key."""
    f = Fernet(key.encode())
    return f.encrypt(data)


def decrypt(data: bytes, key: str) -> bytes:
    """Decrypt data with the given Fernet key.

    Raises SystemExit on decryption failure (wrong key or corrupted data).
    """
    f = Fernet(key.encode())
    try:
        return f.decrypt(data)
    except InvalidToken:
        raise SystemExit(
            "Error: decryption failed. Check that TASKTOOL_FERNET_KEY is correct "
            "and the data is not corrupted."
        )
