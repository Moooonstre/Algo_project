"""Unit tests for backend.feed (proximity score + MergeSort + ranking)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.feed import merge_sort, proximity_score, rank_timeline
from backend.graph import SocialGraph
from backend.posts import Post


def make_post(post_id, author_id, likes):
    return Post(
        post_id=post_id,
        author_id=author_id,
        content=f"post {post_id}",
        created_at="2026-05-31T10:00:00Z",
        likes=list(likes),
    )


class MergeSortTest(unittest.TestCase):
    def test_empty_and_single(self):
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(merge_sort([5]), [5])

    def test_sorts_ascending(self):
        self.assertEqual(merge_sort([5, 2, 8, 1, 9, 3]), [1, 2, 3, 5, 8, 9])

    def test_sorts_descending(self):
        self.assertEqual(
            merge_sort([5, 2, 8, 1], reverse=True), [8, 5, 2, 1]
        )

    def test_is_stable(self):
        # equal keys keep input order (tuples with same first element)
        data = [(1, "a"), (1, "b"), (0, "c"), (1, "d")]
        out = merge_sort(data, key=lambda x: x[0])
        self.assertEqual(out, [(0, "c"), (1, "a"), (1, "b"), (1, "d")])

    def test_matches_builtin_on_random(self):
        data = [7, 3, 9, 1, 1, 4, 8, 2, 5, 0, 6]
        self.assertEqual(merge_sort(data), sorted(data))


class ProximityScoreTest(unittest.TestCase):
    def setUp(self):
        # viewer 1 is friends with 2 and 3 only.
        self.g = SocialGraph()
        self.g.add_users([1, 2, 3, 4, 5])
        self.g.add_friendship(1, 2)
        self.g.add_friendship(1, 3)

    def test_friend_like_worth_10_stranger_1(self):
        # liked by 2 (friend, 10), 3 (friend, 10), 4 (stranger, 1) -> 21
        post = make_post(1, 9, [2, 3, 4])
        self.assertEqual(proximity_score(post, 1, self.g), 21)

    def test_all_strangers(self):
        post = make_post(1, 9, [4, 5])
        self.assertEqual(proximity_score(post, 1, self.g), 2)

    def test_no_likes_is_zero(self):
        self.assertEqual(proximity_score(make_post(1, 9, []), 1, self.g), 0)


class RankTimelineTest(unittest.TestCase):
    def test_ranking_by_proximity_score(self):
        g = SocialGraph()
        g.add_users([1, 2, 3, 4])
        g.add_friendship(1, 2)
        g.add_friendship(1, 3)
        # post 10: liked by friends 2,3 -> 20
        # post 11: liked by stranger 4 -> 1
        # post 12: liked by friend 2 -> 10
        posts = [
            make_post(10, 9, [2, 3]),
            make_post(11, 9, [4]),
            make_post(12, 9, [2]),
        ]
        ranked = rank_timeline(posts, 1, g)
        ids = [p.post_id for p, _ in ranked]
        scores = [s for _, s in ranked]
        self.assertEqual(ids, [10, 12, 11])
        self.assertEqual(scores, [20, 10, 1])

    def test_tie_break_newest_first(self):
        g = SocialGraph()
        g.add_users([1, 2])
        g.add_friendship(1, 2)
        # both liked by friend 2 -> same score 10; newer (higher id) first
        posts = [make_post(10, 9, [2]), make_post(20, 9, [2])]
        ranked = rank_timeline(posts, 1, g)
        self.assertEqual([p.post_id for p, _ in ranked], [20, 10])


if __name__ == "__main__":
    unittest.main()
