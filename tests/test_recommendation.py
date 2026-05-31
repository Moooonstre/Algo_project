"""Unit tests for backend.recommendation (mutual friends, Jaccard, suggestions).

Anchored on LAB 2 Ex.2 (mutual friends as set intersection, Jaccard) and
LAB 6 Ex.3 (friends-of-friends recommendation).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.graph import SocialGraph
from backend.recommendation import (
    jaccard_similarity,
    mutual_friends,
    recommend_friends,
)


def build_graph(n, edges):
    g = SocialGraph()
    g.add_users(range(1, n + 1))
    for a, b in edges:
        g.add_friendship(a, b)
    return g


class MutualFriendsTest(unittest.TestCase):
    def test_intersection(self):
        # 1 and 2 share friends 3 and 4.
        g = build_graph(5, [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4)])
        self.assertEqual(mutual_friends(g, 1, 2), [3, 4])

    def test_no_mutual(self):
        g = build_graph(4, [(1, 2), (3, 4)])
        self.assertEqual(mutual_friends(g, 1, 3), [])

    def test_jaccard_matches_lab2_example_shape(self):
        # friends(1) = {3,4,5}, friends(2) = {3,4,6,7,8}
        # intersection = {3,4} (2), union = {3,4,5,6,7,8} (6) -> 2/6
        g = build_graph(8, [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 6), (2, 7), (2, 8)])
        self.assertAlmostEqual(jaccard_similarity(g, 1, 2), 2 / 6)

    def test_jaccard_empty_union_is_zero(self):
        g = build_graph(2, [])
        self.assertEqual(jaccard_similarity(g, 1, 2), 0.0)


class RecommendFriendsTest(unittest.TestCase):
    def test_friends_of_friends_ranked_by_mutual(self):
        # 1 is friends with 2 and 3.
        # 4 is friend of both 2 and 3  -> 2 mutual friends.
        # 5 is friend of 3 only        -> 1 mutual friend.
        # 6 is a direct friend of 1    -> must NOT be recommended.
        g = build_graph(
            6, [(1, 2), (1, 3), (1, 6), (2, 4), (3, 4), (3, 5)]
        )
        suggestions = recommend_friends(g, 1)
        ids = [s.user_id for s in suggestions]
        self.assertEqual(ids, [4, 5])  # 4 first (2 mutual) then 5 (1 mutual)
        self.assertEqual(suggestions[0].mutual_friends, 2)
        self.assertEqual(suggestions[1].mutual_friends, 1)
        self.assertNotIn(6, ids)  # already a direct friend
        self.assertNotIn(1, ids)  # never recommend self

    def test_limit(self):
        g = build_graph(6, [(1, 2), (1, 3), (2, 4), (3, 4), (3, 5)])
        self.assertEqual(len(recommend_friends(g, 1, limit=1)), 1)

    def test_no_candidates(self):
        g = build_graph(3, [(1, 2)])  # 1 has only friend 2, no friends-of-friends
        self.assertEqual(recommend_friends(g, 1), [])

    def test_unknown_user(self):
        g = build_graph(2, [(1, 2)])
        with self.assertRaises(KeyError):
            recommend_friends(g, 99)


if __name__ == "__main__":
    unittest.main()
