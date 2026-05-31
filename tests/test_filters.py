"""Unit tests for backend.filters (Gate Settings confidence thresholds)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.filters import (
    filter_by_friend_like_threshold,
    filter_recommendations_by_mutual,
    friend_like_count,
)
from backend.graph import SocialGraph
from backend.posts import Post
from backend.recommendation import Suggestion


def make_post(post_id, likes):
    return Post(post_id, 9, f"p{post_id}", "2026-05-31T10:00:00Z", list(likes))


class FriendLikeCountTest(unittest.TestCase):
    def setUp(self):
        self.g = SocialGraph()
        self.g.add_users([1, 2, 3, 4, 5])
        self.g.add_friendship(1, 2)
        self.g.add_friendship(1, 3)  # viewer 1 friends with 2,3

    def test_counts_only_friend_likers(self):
        post = make_post(1, [2, 3, 4, 5])  # 2,3 friends; 4,5 strangers
        self.assertEqual(friend_like_count(post, 1, self.g), 2)

    def test_no_friend_likes(self):
        post = make_post(1, [4, 5])
        self.assertEqual(friend_like_count(post, 1, self.g), 0)


class FilterTimelineTest(unittest.TestCase):
    def setUp(self):
        self.g = SocialGraph()
        self.g.add_users([1, 2, 3, 4])
        self.g.add_friendship(1, 2)
        self.g.add_friendship(1, 3)
        # post A: 2 friend likes ; post B: 1 friend like ; post C: 0 friend likes
        self.ranked = [
            (make_post(10, [2, 3]), 20),
            (make_post(11, [2, 4]), 11),
            (make_post(12, [4]), 1),
        ]

    def test_threshold_zero_keeps_all(self):
        out = filter_by_friend_like_threshold(self.ranked, 1, self.g, 0)
        self.assertEqual(len(out), 3)

    def test_threshold_two(self):
        out = filter_by_friend_like_threshold(self.ranked, 1, self.g, 2)
        self.assertEqual([p.post_id for p, _ in out], [10])

    def test_threshold_one(self):
        out = filter_by_friend_like_threshold(self.ranked, 1, self.g, 1)
        self.assertEqual([p.post_id for p, _ in out], [10, 11])


class FilterRecommendationsTest(unittest.TestCase):
    def test_mutual_threshold(self):
        sugg = [Suggestion(4, 3), Suggestion(5, 2), Suggestion(6, 1)]
        self.assertEqual(
            [s.user_id for s in filter_recommendations_by_mutual(sugg, 2)],
            [4, 5],
        )

    def test_threshold_zero_keeps_all(self):
        sugg = [Suggestion(4, 3), Suggestion(5, 1)]
        self.assertEqual(len(filter_recommendations_by_mutual(sugg, 0)), 2)


if __name__ == "__main__":
    unittest.main()
