"""Unit tests for backend.social_store.SocialStore (graph + JSON persistence)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.social_store import FriendshipError, SocialStore


class SocialStoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "friends.json"
        self.store = SocialStore(self.path)
        for uid in (1, 2, 3, 4):
            self.store.ensure_user(uid)

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_and_query_friend(self):
        self.assertTrue(self.store.add_friend(1, 2))
        self.assertTrue(self.store.are_friends(1, 2))
        self.assertEqual(self.store.friends(1), [2])
        self.assertEqual(self.store.friend_count(1), 1)

    def test_add_friend_idempotent(self):
        self.store.add_friend(1, 2)
        self.assertFalse(self.store.add_friend(2, 1))

    def test_self_friendship_rejected(self):
        with self.assertRaises(FriendshipError):
            self.store.add_friend(1, 1)

    def test_unknown_user_rejected(self):
        with self.assertRaises(FriendshipError):
            self.store.add_friend(1, 999)

    def test_remove_friend(self):
        self.store.add_friend(1, 2)
        self.assertTrue(self.store.remove_friend(1, 2))
        self.assertEqual(self.store.friends(1), [])

    def test_persistence_round_trip(self):
        self.store.add_friend(1, 2)
        self.store.add_friend(2, 3)
        # Reload from disk into a fresh store.
        reloaded = SocialStore(self.path)
        self.assertTrue(reloaded.are_friends(1, 2))
        self.assertTrue(reloaded.are_friends(2, 3))
        self.assertEqual(reloaded.friends(2), [1, 3])
        # Isolated node 4 must survive the round-trip too.
        self.assertTrue(reloaded.has_user(4))

    def test_graph_property_exposes_algorithms(self):
        self.store.add_friend(1, 2)
        self.store.add_friend(2, 3)
        # friends-of-friends of 1 (distance 2) is {3}
        self.assertEqual(self.store.graph.nodes_at_distance(1, 2), {3})


if __name__ == "__main__":
    unittest.main()
