"""User store: BST keyed by user_id + hash map keyed by username.

This module is the bridge between the data structures from the course and the
HTTP layer. We follow the recommendation in LAB8's final integration question:

    "use a BST for user lookup by id, and a hash map for username -> id"

so we get O(log n) ordered access by id (useful for a future
``inorder_traversal`` of users in id order) plus O(1) average-case lookup by
username, which is the field the login form uses.

Persistence is handled with a single JSON file (the only "database" the
course material covers is the basic ``File`` type, mentioned in Lecture 3,
slide 6).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Iterator

from .auth import hash_password, verify_password
from .bst import BST


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÿ' \-]{1,50}$")
PASSWORD_MIN_LEN = 8


class ValidationError(ValueError):
    """Raised when an input does not satisfy the registration constraints."""


class DuplicateUserError(ValueError):
    """Raised when a username or email is already taken."""


@dataclass
class User:
    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    birth_date: str  # ISO-8601 YYYY-MM-DD
    salt: str
    password_hash: str
    created_at: str

    def public_dict(self) -> dict:
        """Return a serialisable view without the password material."""
        d = asdict(self)
        d.pop("salt")
        d.pop("password_hash")
        return d


def _validate_birth_date(raw: str) -> str:
    """Return the date in ISO format if it is a real, past date."""
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError("birth_date must be YYYY-MM-DD") from exc
    if parsed > datetime.now(timezone.utc).date():
        raise ValidationError("birth_date is in the future")
    return parsed.isoformat()


def validate_registration(payload: dict) -> dict:
    """Check and normalise the fields of a registration request.

    Returns the cleaned payload (whitespace stripped, dates parsed) or raises
    ``ValidationError`` with a human-readable message.
    """
    cleaned: dict[str, str] = {}
    for field in (
        "username",
        "email",
        "first_name",
        "last_name",
        "birth_date",
        "password",
    ):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"missing field: {field}")
        cleaned[field] = value.strip()

    if not USERNAME_PATTERN.match(cleaned["username"]):
        raise ValidationError(
            "username must be 3-30 chars, letters/digits/underscore only"
        )
    if not EMAIL_PATTERN.match(cleaned["email"]):
        raise ValidationError("email is not valid")
    if not NAME_PATTERN.match(cleaned["first_name"]):
        raise ValidationError("first_name is not valid")
    if not NAME_PATTERN.match(cleaned["last_name"]):
        raise ValidationError("last_name is not valid")
    cleaned["birth_date"] = _validate_birth_date(cleaned["birth_date"])
    if len(cleaned["password"]) < PASSWORD_MIN_LEN:
        raise ValidationError(
            f"password must be at least {PASSWORD_MIN_LEN} characters"
        )
    return cleaned


class UserStore:
    """In-memory user database, persisted to a JSON file.

    Internal state:
        users_by_id        : BST keyed by integer user_id
        username_to_id     : hash map (dict) for O(1) username lookup
        email_to_id        : hash map (dict) for O(1) email lookup
        next_id            : monotonically increasing integer
    """

    def __init__(self, db_path: str | os.PathLike) -> None:
        self._db_path = Path(db_path)
        self._lock = RLock()
        self._users_by_id: BST = BST()
        self._username_to_id: dict[str, int] = {}
        self._email_to_id: dict[str, int] = {}
        self._next_id: int = 1
        self._load()

    # --- Public API -----------------------------------------------------------

    def register(self, payload: dict) -> User:
        cleaned = validate_registration(payload)
        with self._lock:
            uname_key = cleaned["username"].lower()
            email_key = cleaned["email"].lower()
            if uname_key in self._username_to_id:
                raise DuplicateUserError("username already taken")
            if email_key in self._email_to_id:
                raise DuplicateUserError("email already registered")

            salt, password_hash = hash_password(cleaned["password"])
            user = User(
                user_id=self._next_id,
                username=cleaned["username"],
                email=cleaned["email"],
                first_name=cleaned["first_name"],
                last_name=cleaned["last_name"],
                birth_date=cleaned["birth_date"],
                salt=salt,
                password_hash=password_hash,
                created_at=datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            )
            self._users_by_id.insert(user.user_id, user)
            self._username_to_id[uname_key] = user.user_id
            self._email_to_id[email_key] = user.user_id
            self._next_id += 1
            self._save()
            return user

    def authenticate(self, username_or_email: str, password: str) -> User | None:
        """Return the matching User on success, else None."""
        with self._lock:
            user = self.find_by_username(username_or_email) or self.find_by_email(
                username_or_email
            )
            if user is None:
                return None
            if not verify_password(password, user.salt, user.password_hash):
                return None
            return user

    def find_by_id(self, user_id: int) -> User | None:
        value = self._users_by_id.search(user_id)
        return value if isinstance(value, User) else None

    def find_by_username(self, username: str) -> User | None:
        user_id = self._username_to_id.get(username.lower())
        return self.find_by_id(user_id) if user_id is not None else None

    def find_by_email(self, email: str) -> User | None:
        user_id = self._email_to_id.get(email.lower())
        return self.find_by_id(user_id) if user_id is not None else None

    def all_users(self) -> Iterator[User]:
        for _, value in self._users_by_id.in_order():
            if isinstance(value, User):
                yield value

    def size(self) -> int:
        return self._users_by_id.size()

    # --- Persistence ----------------------------------------------------------

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        with self._db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._next_id = int(data.get("next_id", 1))
        for record in data.get("users", []):
            user = User(**record)
            self._users_by_id.insert(user.user_id, user)
            self._username_to_id[user.username.lower()] = user.user_id
            self._email_to_id[user.email.lower()] = user.user_id

    def _save(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        records = [asdict(user) for user in self.all_users()]
        tmp_path = self._db_path.with_suffix(self._db_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(
                {"next_id": self._next_id, "users": records},
                f,
                indent=2,
                ensure_ascii=False,
            )
        os.replace(tmp_path, self._db_path)
