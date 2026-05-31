"""Friend recommendation — the ASNAP "Social Discovery" service.

Every procedure here comes straight from the course material; nothing is
invented:

* **mutual friends** = the *intersection of two friend sets* — exactly
  LAB 2 Ex.2 "Mutual Friends Detection Using Sets" (``Intersection(set1, set2)``);
* **Jaccard similarity** = ``|intersection| / |union|`` of the two friend sets —
  the "mutual friend coefficient / Jaccard similarity of their social circles"
  of LAB 2 Ex.2 (requirement 3);
* **friend recommendation** = *friends of friends not already friends* — the
  ``recommend_friends`` of LAB 6 Ex.3 (and the 2nd-degree friend-of-friend
  suggestion of LAB 2 Ex.2). Candidates are produced by the BFS-distance-2
  primitive (:meth:`SocialGraph.nodes_at_distance`, Lecture 8 / LAB 6 Ex.3) and
  ranked by their number of mutual friends.

All of this is read-only over :class:`backend.graph.SocialGraph`, whose
adjacency is already stored as Python ``set`` objects, so the set operations of
LAB 2 are used directly.
"""

from __future__ import annotations

from typing import List, NamedTuple, Optional

from .graph import SocialGraph


class Suggestion(NamedTuple):
    user_id: int
    mutual_friends: int


def mutual_friends(graph: SocialGraph, a: int, b: int) -> List[int]:
    """Return the sorted list of users who are friends with both ``a`` and ``b``.

    Set intersection of the two adjacency sets (LAB 2 Ex.2). Cost is
    O(min(deg(a), deg(b))) — the cheaper of the two sets drives the scan.
    """
    common = graph.neighbours(a) & graph.neighbours(b)
    return sorted(common)


def jaccard_similarity(graph: SocialGraph, a: int, b: int) -> float:
    """Return the Jaccard similarity of the two friend circles (LAB 2 Ex.2).

    ``|friends(a) ∩ friends(b)| / |friends(a) ∪ friends(b)|`` — the "mutual
    friend coefficient". By convention two users with no friends at all have
    similarity 0 (empty union). Range [0, 1].
    """
    fa = graph.neighbours(a)
    fb = graph.neighbours(b)
    union = fa | fb
    if not union:
        return 0.0
    return len(fa & fb) / len(union)


def recommend_friends(
    graph: SocialGraph, user_id: int, limit: Optional[int] = None
) -> List[Suggestion]:
    """Recommend friends of friends not already connected (LAB 6 Ex.3).

    A candidate is a user at BFS distance exactly 2 — a friend of a friend who
    is neither the user nor an existing direct friend. Each candidate is ranked
    by its number of **mutual friends** with the user (LAB 2 Ex.2): more common
    friends ⇒ stronger suggestion. Ties are broken by ``user_id`` ascending for
    reproducibility.

    Cost: one BFS to distance 2 — O(N + E) — plus O(deg) per candidate for the
    mutual-friend count.

    Args:
        graph: the social graph.
        user_id: the user asking for suggestions.
        limit: keep only the top ``limit`` suggestions (None = all).

    Returns:
        a list of :class:`Suggestion` sorted by ``mutual_friends`` desc, id asc.
    """
    if not graph.has_user(user_id):
        raise KeyError(f"unknown user {user_id}")

    direct_friends = graph.neighbours(user_id)
    # Candidates = friends of friends not already friends (LAB 6 Ex.3):
    candidates = graph.nodes_at_distance(user_id, 2)

    suggestions: List[Suggestion] = []
    for candidate in candidates:
        # nodes_at_distance(2) already excludes the user and direct friends,
        # but we stay defensive (the "rigorous reader" of Lecture 2).
        if candidate == user_id or candidate in direct_friends:
            continue
        common = len(direct_friends & graph.neighbours(candidate))
        suggestions.append(Suggestion(candidate, common))

    suggestions.sort(key=lambda s: (-s.mutual_friends, s.user_id))
    if limit is not None:
        suggestions = suggestions[:limit]
    return suggestions
