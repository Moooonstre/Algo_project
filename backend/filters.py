"""Gate Settings — confidence-threshold filters (ASNAP / Social Gate slide 5).

The project's "Gate Settings" let a user hide low-confidence content:

* **friend-like confidence threshold**: hide posts that have fewer than ``k``
  likes coming *from the viewer's friends* (project: "cacher les posts en
  dessous d'un nombre de likes d'amis"; slide 5 "3 friends likes threshold");
* **mutual-friends threshold**: hide friend suggestions backed by fewer than
  ``k`` mutual friends (slide 5 "Mutual friends threshold").

These are simple counting filters built on top of the course primitives
(``are_friends`` from the graph, Lecture 8 / LAB 6; mutual-friend count from
LAB 2 Ex.2). The threshold semantics themselves are project-subject material,
not a course algorithm — we keep that distinction explicit.
"""

from __future__ import annotations

from typing import List, Tuple

from .graph import SocialGraph
from .posts import Post
from .recommendation import Suggestion


def friend_like_count(post: Post, viewer_id: int, graph: SocialGraph) -> int:
    """Number of likes on ``post`` that come from direct friends of the viewer.

    O(L) — one O(1)-average ``are_friends`` test per liker.
    """
    if not graph.has_user(viewer_id):
        return 0
    return sum(1 for liker in post.likes if graph.are_friends(viewer_id, liker))


def filter_by_friend_like_threshold(
    ranked: List[Tuple[Post, int]],
    viewer_id: int,
    graph: SocialGraph,
    min_friend_likes: int,
) -> List[Tuple[Post, int]]:
    """Keep only posts with at least ``min_friend_likes`` likes from friends.

    ``ranked`` is the ``[(post, score), ...]`` list produced by the timeline
    ranking; order is preserved. ``min_friend_likes <= 0`` keeps everything.
    O(P · L̄).
    """
    if min_friend_likes <= 0:
        return list(ranked)
    return [
        (post, score)
        for post, score in ranked
        if friend_like_count(post, viewer_id, graph) >= min_friend_likes
    ]


def filter_recommendations_by_mutual(
    suggestions: List[Suggestion], min_mutual: int
) -> List[Suggestion]:
    """Keep only suggestions backed by at least ``min_mutual`` mutual friends.

    Order is preserved. ``min_mutual <= 0`` keeps everything. O(S).
    """
    if min_mutual <= 0:
        return list(suggestions)
    return [s for s in suggestions if s.mutual_friends >= min_mutual]
