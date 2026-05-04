"""Unit tests for backend.user_store.UserStore."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.user_store import (
    DuplicateUserError,
    UserStore,
    ValidationError,
    validate_registration,
)


VALID_PAYLOAD = {
    "username": "alice_42",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Martin",
    "birth_date": "2002-04-15",
    "password": "supersecret1",
}


class ValidationTest(unittest.TestCase):
    def test_valid_payload(self):
        cleaned = validate_registration(VALID_PAYLOAD)
        self.assertEqual(cleaned["username"], "alice_42")
        self.assertEqual(cleaned["birth_date"], "2002-04-15")

    def test_missing_field(self):
        payload = dict(VALID_PAYLOAD)
        payload.pop("email")
        with self.assertRaises(ValidationError):
            validate_registration(payload)

    def test_short_password(self):
        payload = dict(VALID_PAYLOAD, password="short1")
        with self.assertRaises(ValidationError):
            validate_registration(payload)

    def test_bad_email(self):
        payload = dict(VALID_PAYLOAD, email="not-an-email")
        with self.assertRaises(ValidationError):
            validate_registration(payload)

    def test_bad_username(self):
        payload = dict(VALID_PAYLOAD, username="a!")
        with self.assertRaises(ValidationError):
            validate_registration(payload)

    def test_future_birth_date(self):
        payload = dict(VALID_PAYLOAD, birth_date="2999-01-01")
        with self.assertRaises(ValidationError):
            validate_registration(payload)


class UserStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "users.json"
        self.store = UserStore(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_register_and_lookup(self):
        user = self.store.register(VALID_PAYLOAD)
        self.assertEqual(user.user_id, 1)
        self.assertEqual(self.store.size(), 1)
        self.assertEqual(self.store.find_by_id(1), user)
        self.assertEqual(self.store.find_by_username("alice_42"), user)
        self.assertEqual(self.store.find_by_email("ALICE@example.com"), user)

    def test_duplicate_username(self):
        self.store.register(VALID_PAYLOAD)
        with self.assertRaises(DuplicateUserError):
            self.store.register(dict(VALID_PAYLOAD, email="bob@example.com"))

    def test_duplicate_email(self):
        self.store.register(VALID_PAYLOAD)
        with self.assertRaises(DuplicateUserError):
            self.store.register(dict(VALID_PAYLOAD, username="bob_99"))

    def test_authenticate(self):
        self.store.register(VALID_PAYLOAD)
        good = self.store.authenticate("alice_42", "supersecret1")
        self.assertIsNotNone(good)
        self.assertEqual(good.username, "alice_42")
        bad = self.store.authenticate("alice_42", "wrong-password")
        self.assertIsNone(bad)
        self.assertIsNone(self.store.authenticate("ghost", "supersecret1"))

    def test_authenticate_with_email(self):
        self.store.register(VALID_PAYLOAD)
        user = self.store.authenticate("alice@example.com", "supersecret1")
        self.assertIsNotNone(user)

    def test_password_not_in_public_dict(self):
        user = self.store.register(VALID_PAYLOAD)
        public = user.public_dict()
        self.assertNotIn("password_hash", public)
        self.assertNotIn("salt", public)

    def test_persistence_round_trip(self):
        self.store.register(VALID_PAYLOAD)
        self.store.register(
            dict(
                VALID_PAYLOAD,
                username="bob",
                email="bob@example.com",
                first_name="Bob",
            )
        )
        # Re-open the file using a fresh store: data should be reloaded.
        reloaded = UserStore(self.db)
        self.assertEqual(reloaded.size(), 2)
        alice = reloaded.find_by_username("alice_42")
        self.assertIsNotNone(alice)
        # Authenticate against the reloaded data to make sure salts/hashes
        # round-tripped through JSON correctly.
        self.assertIsNotNone(reloaded.authenticate("alice_42", "supersecret1"))

    def test_persistence_file_layout(self):
        self.store.register(VALID_PAYLOAD)
        with self.db.open() as f:
            data = json.load(f)
        self.assertEqual(data["next_id"], 2)
        self.assertEqual(len(data["users"]), 1)
        record = data["users"][0]
        self.assertIn("salt", record)
        self.assertIn("password_hash", record)


if __name__ == "__main__":
    unittest.main()
