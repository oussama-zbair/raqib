"""CIN encryption helpers.

CIN is sensitive. It is stored as Fernet ciphertext and decrypted only in memory,
at PDF roll-call time, by the monitor job.
"""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().cin_encryption_key
    if not key:
        raise RuntimeError(
            "CIN_ENCRYPTION_KEY is not set. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def encrypt_cin(cin: str) -> str:
    """Encrypt a plaintext CIN into a storable token."""
    return _fernet().encrypt(cin.strip().upper().encode()).decode()


def decrypt_cin(token: str) -> str:
    """Decrypt a stored token back to the plaintext CIN (in memory only)."""
    return _fernet().decrypt(token.encode()).decode()


def cin_last4(cin: str) -> str:
    """Non-sensitive display hint, e.g. 'AB123456' -> '3456'."""
    digits = "".join(ch for ch in cin if ch.isdigit())
    return digits[-4:] if digits else cin[-4:]
