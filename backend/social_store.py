"""Bridge between the user database and the friendship graph.

``SocialStore`` keeps a :class:`backend.graph.SocialGraph` whose nodes are the
``user_id`` values managed by :class:`backend.user_store.UserStore`, and persists
the friendships to a JSON file — the same ``File``-based persistence the course
uses for users (Lecture 3). No SGBD is involved, in line with the team's
course-aligned choice.

File format (``data/friends.json``)::

    {
      "nodes": [1, 2, 3],
      "edges": [[1, 2], [2, 3]]      # each undirected edge stored once, low-high
    }

``nodes`` is stored explicitly so that a user with no friendships yet is still
restored as an isolated node after a restart.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Iterable, List, Tuple

from .graph import SocialGraph


class FriendshipError(ValueError):
    """Raised when a friendship operation references an unknown user."""


class SocialStore:
    """Friendship graph over user_ids, persisted to a JSON file."""

    def __init__(self, db_path: str | os.PathLike) -> None:
        self._db_path = Path(db_path)
        self._lock = RLock()
        self._graph = SocialGraph()
        self._load()

    # --- Membership -----------------------------------------------------------

    def ensure_user(self, user_id: int) -> None:
        """Make sure ``user_id`` is a node of the graph (called on register)."""
        with self._lock:
            if self._graph.add_user(user_id):
                self._save()

    def sync_users(self, user_ids: Iterable[int]) -> None:
        """Add every id as a node (used at startup to seed from the UserStore)."""
        with self._lock:
            changed = False
            for uid in user_ids:
                changed = self._graph.add_user(uid) or changed
            if changed:
                self._save()

    def has_user(self, user_id: int) -> bool:
        return self._graph.has_user(user_id)

    # --- Friendships ----------------------------------------------------------

    def add_friend(self, a: int, b: int) -> bool:
        """Create a mutual friendship. Return True if it was new."""
        with self._lock:
            if a == b:
                raise FriendshipError("a user cannot befriend themselves")
            self._require_user(a)
            self._require_user(b)
            created = self._graph.add_friendship(a, b)
            if created:
                self._save()
            return created

    def remove_friend(self, a: int, b: int) -> bool:
        with self._lock:
            removed = self._graph.remove_friendship(a, b)
            if removed:
                self._save()
            return removed

    def are_friends(self, a: int, b: int) -> bool:
        return self._graph.are_friends(a, b)

    def friends(self, user_id: int) -> List[int]:
        """Return the direct friends of ``user_id`` sorted by id."""
        self._require_user(user_id)
        return sorted(self._graph.neighbours(user_id))

    def friend_count(self, user_id: int) -> int:
        self._require_user(user_id)
        return self._graph.degree(user_id)

    # --- Access to the underlying graph (read-only algorithms) ----------------

    @property
    def graph(self) -> SocialGraph:
        """The live graph, for the recommendation / ranking algorithms."""
        return self._graph

    def _require_user(self, user_id: int) -> None:
        if not self._graph.has_user(user_id):
            raise FriendshipError(f"unknown user {user_id}")

    # --- Persistence (Lecture 3 — type File) ----------------------------------

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        with self._db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for uid in data.get("nodes", []):
            self._graph.add_user(int(uid))
        for edge in data.get("edges", []):
            a, b = int(edge[0]), int(edge[1])
            self._graph.add_user(a)
            self._graph.add_user(b)
            self._graph.add_friendship(a, b)

    def _save(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        nodes: List[int] = sorted(self._graph.users())
        edges: List[Tuple[int, int]] = list(self._graph.edges())
        tmp_path = self._db_path.with_suffix(self._db_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(
                {"nodes": nodes, "edges": [list(e) for e in edges]},
                f,
                indent=2,
            )
        os.replace(tmp_path, self._db_path)
