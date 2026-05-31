"""Dataset generators — build SocialGraph instances of varying sizes.

The project's section 3 asks us to "test the platform with datasets of varying
sizes" and "analyze the efficiency of the algorithms". This module produces the
graphs used both by the tests (small, deterministic) and by ``benchmark.py``
(increasing sizes). It also covers the canonical shapes whose properties the
labs reason about: empty, path, star, complete, and random (Erdős–Rényi).

Pure generation — no file I/O, no external library. ``seed`` makes the random
generator reproducible.
"""

from __future__ import annotations

import random
from typing import Optional

from .graph import SocialGraph


def empty_graph(n: int) -> SocialGraph:
    """``n`` users, no friendships (every user isolated)."""
    g = SocialGraph()
    g.add_users(range(1, n + 1))
    return g


def path_graph(n: int) -> SocialGraph:
    """Users 1..n connected in a line 1-2-3-...-n."""
    g = empty_graph(n)
    for i in range(1, n):
        g.add_friendship(i, i + 1)
    return g


def star_graph(n: int) -> SocialGraph:
    """User 1 (the centre) is friends with every other user."""
    g = empty_graph(n)
    for i in range(2, n + 1):
        g.add_friendship(1, i)
    return g


def complete_graph(n: int) -> SocialGraph:
    """Every pair of users is friends (K_n)."""
    g = empty_graph(n)
    nodes = list(range(1, n + 1))
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            g.add_friendship(a, b)
    return g


def random_social_graph(
    n: int, edge_probability: float = 0.1, seed: Optional[int] = None
) -> SocialGraph:
    """Erdős–Rényi style random friendship graph.

    Each of the n·(n-1)/2 possible friendships exists independently with
    probability ``edge_probability``. ``seed`` makes it reproducible. O(N^2).
    """
    if not 0.0 <= edge_probability <= 1.0:
        raise ValueError("edge_probability must be in [0, 1]")
    g = empty_graph(n)
    rng = random.Random(seed)
    nodes = list(range(1, n + 1))
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if rng.random() < edge_probability:
                g.add_friendship(a, b)
    return g
