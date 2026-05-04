"""Unit tests for backend.auth (password hashing + session store)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth import (
    SessionStore,
    hash_password,
    new_session_token,
    verify_password,
)


class HashPasswordTest(unittest.TestCase):
    def test_salt_is_random(self):
        salt_a, hash_a = hash_password("hunter2hunter2")
        salt_b, hash_b = hash_password("hunter2hunter2")
        self.assertNotEqual(salt_a, salt_b)
        self.assertNotEqual(hash_a, hash_b)

    def test_same_salt_same_hash(self):
        salt, digest = hash_password("hunter2hunter2")
        _, repeated = hash_password("hunter2hunter2", salt)
        self.assertEqual(digest, repeated)

    def test_verify_password_success(self):
        salt, digest = hash_password("correct-horse-battery")
        self.assertTrue(verify_password("correct-horse-battery", salt, digest))

    def test_verify_password_failure(self):
        salt, digest = hash_password("correct-horse-battery")
        self.assertFalse(verify_password("wrong-password!", salt, digest))


class SessionTokenTest(unittest.TestCase):
    def test_token_uniqueness_and_length(self):
        seen = {new_session_token() for _ in range(2_000)}
        self.assertEqual(len(seen), 2_000)
        for token in seen:
            self.assertEqual(len(token), 64)  # 32 bytes hex-encoded


class SessionStoreTest(unittest.TestCase):
    def test_create_get_revoke(self):
        sessions = SessionStore()
        token = sessions.create(42)
        self.assertEqual(sessions.get(token), 42)
        self.assertEqual(sessions.size(), 1)
        self.assertTrue(sessions.revoke(token))
        self.assertIsNone(sessions.get(token))
        self.assertFalse(sessions.revoke(token))


if __name__ == "__main__":
    unittest.main()
