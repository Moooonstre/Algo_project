"""Password hashing and session token generation.

The cryptographic primitives used here are taken from the Python standard
library (`hashlib`, `secrets`, `hmac`). The course does not cover cryptography,
so we keep the scheme intentionally simple:

    stored = sha256( salt || password ).hex()

with a per-user random salt. Verification recomputes the digest and uses
``hmac.compare_digest`` to defend against timing attacks.

Session tokens are random 32-byte hex strings produced by ``secrets.token_hex``,
indexed by a hash map (``token -> user_id``) — see Lecture 5 (hash maps appear
in LAB1 Ex6 and LAB8 final integration as the canonical "fast lookup" structure).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


SALT_BYTES = 16
TOKEN_BYTES = 32


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """Hash a password with SHA-256 and a per-user random salt.

    If ``salt_hex`` is None a fresh salt is generated. Returns a tuple
    ``(salt_hex, hash_hex)`` so the caller can persist both fields.
    """
    if salt_hex is None:
        salt_hex = secrets.token_hex(SALT_BYTES)
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return salt_hex, digest


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """Return True if ``password`` matches the stored ``(salt, hash)`` pair.

    Uses a constant-time comparison so an attacker cannot learn the prefix of
    the stored digest from response timing.
    """
    _, candidate = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate, expected_hash_hex)


def new_session_token() -> str:
    """Return a random hex token suitable for use as a session id."""
    return secrets.token_hex(TOKEN_BYTES)


class SessionStore:
    """Hash map ``token -> user_id`` of active sessions.

    Using a hash map gives O(1) average-case lookup, the same property
    discussed for hash-based representations of linear data in LAB1 Ex6 and
    used as the baseline in LAB8's final integration question.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, int] = {}

    def create(self, user_id: int) -> str:
        token = new_session_token()
        self._tokens[token] = user_id
        return token

    def get(self, token: str) -> int | None:
        return self._tokens.get(token)

    def revoke(self, token: str) -> bool:
        return self._tokens.pop(token, None) is not None

    def size(self) -> int:
        return len(self._tokens)
