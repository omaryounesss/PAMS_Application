"""Security helpers for password hashing and verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass


PBKDF2_ITERATIONS = 240_000


@dataclass(frozen=True)
class PasswordHash:
    hash_b64: str
    salt_b64: str


def hash_password(plain_text: str, salt: bytes | None = None) -> PasswordHash:
    if len(plain_text) < 8:
        raise ValueError("Password must be at least 8 characters")

    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain_text.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32
    )
    return PasswordHash(
        hash_b64=base64.b64encode(digest).decode("ascii"),
        salt_b64=base64.b64encode(salt).decode("ascii"),
    )


def verify_password(plain_text: str, hash_b64: str, salt_b64: str) -> bool:
    salt = base64.b64decode(salt_b64.encode("ascii"))
    expected = base64.b64decode(hash_b64.encode("ascii"))
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain_text.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32
    )
    return hmac.compare_digest(digest, expected)
