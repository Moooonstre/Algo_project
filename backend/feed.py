"""Gate Timeline — proximity score + MergeSort ranking.

Two course-anchored pieces, nothing invented:

* **Proximity score** (project brief, Main Algorithms slide 6): each post is
  weighted by *who* liked it relative to the viewer — a like from a friend is
  worth 10 points, a like from a stranger 1 point. "Friend" means a direct
  friend (BFS distance 1) in the :class:`backend.graph.SocialGraph`. This is a
  weighted count, in the spirit of the weighted ``engagement_score`` of LAB 3
  Ex.3 (likes/comments/shares with different weights).
* **MergeSort** (our own Divide & Conquer implementation): sorts the timeline
  by score — exactly the ``merge_sort_by_engagement`` of LAB 4 Ex.2, and the
  Merge Sort of Lecture 9 (divide into halves, conquer recursively, merge;
  O(n log n)). All ordering uses this own implementation, not a library sort,
  as the ASNAP brief requires.
"""

from __future__ import annotations

from typing import Callable, List, Tuple, TypeVar

from .graph import SocialGraph
from .posts import Post

FRIEND_LIKE_POINTS = 10
STRANGER_LIKE_POINTS = 1

T = TypeVar("T")


# --- Proximity score (project slide 6) ---------------------------------------

def proximity_score(post: Post, viewer_id: int, graph: SocialGraph) -> int:
    """Score a post for a given viewer.

    For every user who liked the post: +10 if they are a direct friend of the
    viewer, +1 otherwise (project Main Algorithms, slide 6). O(L) where L is the
    number of likes (each ``are_friends`` test is O(1) average on the adjacency
    sets).
    """
    score = 0
    viewer_in_graph = graph.has_user(viewer_id)
    for liker in post.likes:
        if viewer_in_graph and graph.are_friends(viewer_id, liker):
            score += FRIEND_LIKE_POINTS
        else:
            score += STRANGER_LIKE_POINTS
    return score


# --- MergeSort (LAB 4 Ex.2 / Lecture 9) --------------------------------------

def merge_sort(
    items: List[T],
    key: Callable[[T], object] = lambda x: x,
    reverse: bool = False,
) -> List[T]:
    """Sort ``items`` with our own Divide & Conquer MergeSort.

    Stable. Divide the list into halves, sort each recursively, then merge
    (Lecture 9 classification of Merge Sort; LAB 4 Ex.2 ``merge_sort_by_*``).
    Time O(n log n), space O(n). ``reverse=True`` sorts in descending key order.
    """
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return _merge(left, right, key, reverse)


def _merge(
    left: List[T], right: List[T], key: Callable[[T], object], reverse: bool
) -> List[T]:
    """Merge two sorted halves, keeping stability (left wins on ties)."""
    result: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        lk, rk = key(left[i]), key(right[j])
        take_left = (lk >= rk) if reverse else (lk <= rk)
        if take_left:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# --- Timeline ranking ---------------------------------------------------------

def rank_timeline(
    posts: List[Post], viewer_id: int, graph: SocialGraph
) -> List[Tuple[Post, int]]:
    """Return ``[(post, score), ...]`` ranked from most to least relevant.

    Scores each post with :func:`proximity_score`, then orders by score
    descending with our :func:`merge_sort`. Ties are made deterministic (newest
    first) by a first stable MergeSort pass on ``post_id`` descending; the second
    stable pass on score then preserves that order for equal scores. No library
    sort is used. O(P · L̄ + P log P).
    """
    scored = [
        (post, proximity_score(post, viewer_id, graph)) for post in posts
    ]
    # First pass: newest first (stable tie-break baseline), with our MergeSort.
    by_recency = merge_sort(scored, key=lambda pair: pair[0].post_id, reverse=True)
    # Second pass: by score descending; stability keeps "newest first" on ties.
    return merge_sort(by_recency, key=lambda pair: pair[1], reverse=True)
