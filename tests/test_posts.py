"""Unit tests for backend.posts.PostStore (create / like / persistence)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.posts import PostError, PostStore


class PostStoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "posts.json"
        self.store = PostStore(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_post(self):
        p = self.store.create_post(author_id=1, content="hello world")
        self.assertEqual(p.post_id, 1)
        self.assertEqual(p.author_id, 1)
        self.assertEqual(p.content, "hello world")
        self.assertEqual(p.likes, [])
        self.assertEqual(self.store.size(), 1)

    def test_empty_content_rejected(self):
        with self.assertRaises(PostError):
            self.store.create_post(1, "   ")

    def test_too_long_content_rejected(self):
        with self.assertRaises(PostError):
            self.store.create_post(1, "x" * 501)

    def test_like_and_unlike(self):
        p = self.store.create_post(1, "hi")
        self.assertTrue(self.store.like_post(p.post_id, 2))
        self.assertFalse(self.store.like_post(p.post_id, 2))  # idempotent
        self.assertIn(2, self.store.get_post(p.post_id).likes)
        self.assertTrue(self.store.unlike_post(p.post_id, 2))
        self.assertFalse(self.store.unlike_post(p.post_id, 2))

    def test_like_unknown_post(self):
        with self.assertRaises(PostError):
            self.store.like_post(999, 1)

    def test_posts_by_authors(self):
        self.store.create_post(1, "a")
        self.store.create_post(2, "b")
        self.store.create_post(1, "c")
        got = [p.content for p in self.store.posts_by_authors({1})]
        self.assertEqual(got, ["a", "c"])

    def test_persistence_round_trip(self):
        p = self.store.create_post(1, "persisted")
        self.store.like_post(p.post_id, 2)
        reloaded = PostStore(self.path)
        rp = reloaded.get_post(p.post_id)
        self.assertEqual(rp.content, "persisted")
        self.assertEqual(rp.likes, [2])
        # next_id preserved: a new post gets id 2
        self.assertEqual(reloaded.create_post(1, "next").post_id, 2)


if __name__ == "__main__":
    unittest.main()
