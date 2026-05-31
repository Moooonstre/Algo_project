"""Undirected social graph: the core data structure of the ASNAP engine.

Reference: Lecture 8 (*Graph Data Structures*) and **LAB 6 — Basics of Graphs**.
The project brief (ASNAP) requires that *all fundamental graph algorithms be our
own implementation* and that *the system be built around a graph-based model*,
so this module deliberately uses only plain Python containers — no library does
the graph work for us.

Model
-----
* Nodes  : ``user_id`` (integers), one per registered user.
* Edges  : friendships, **undirected** (if ``a`` is a friend of ``b`` then ``b``
  is a friend of ``a``). This matches the "friends' friends" wording of the
  Social Gate slide 6 and the undirected friendship graphs of LAB 6 / LAB 9 /
  LAB 10.

Two representations are kept available, exactly as contrasted in LAB 6 Ex.1:

* an **adjacency list** (``dict[int, set[int]]``) — the primary structure, giving
  O(degree) neighbour iteration and O(N + E) traversals;
* an **adjacency matrix** built on demand by :meth:`to_adjacency_matrix` — handy
  for the density / complete-graph reasoning of the LAB 9 / LAB 10 questions.

Complexity (N = number of nodes, E = number of edges)
-----------------------------------------------------
==============================  ===================
Operation                       Complexity
==============================  ===================
add_user / has_user             O(1) average
add_friendship / remove_...     O(1) average
neighbours / degree             O(1) / O(degree)
bfs_levels / shortest_path      O(N + E)
dfs_preorder                    O(N + E)
connected_components            O(N + E)
to_adjacency_matrix             O(N^2)
==============================  ===================
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple


class SocialGraph:
    """An undirected, unweighted friendship graph keyed by integer user_id."""

    def __init__(self) -> None:
        # Adjacency list: user_id -> set of friend user_ids (LAB 6 Ex.1).
        self._adj: Dict[int, Set[int]] = {}

    # --- Nodes ----------------------------------------------------------------

    def add_user(self, user_id: int) -> bool:
        """Register ``user_id`` as a node. Return True if it was newly added."""
        if user_id in self._adj:
            return False
        self._adj[user_id] = set()
        return True

    def remove_user(self, user_id: int) -> bool:
        """Remove a node and every friendship that touches it. O(degree)."""
        if user_id not in self._adj:
            return False
        for friend in self._adj[user_id]:
            self._adj[friend].discard(user_id)
        del self._adj[user_id]
        return True

    def has_user(self, user_id: int) -> bool:
        return user_id in self._adj

    def users(self) -> Iterator[int]:
        return iter(self._adj.keys())

    def user_count(self) -> int:
        return len(self._adj)

    # --- Edges (friendships) --------------------------------------------------

    def add_friendship(self, a: int, b: int) -> bool:
        """Create an undirected friendship between ``a`` and ``b``.

        Both endpoints must already be nodes (raise ``KeyError`` otherwise, the
        same defensive convention as ``BST.insert``). Self-loops are rejected:
        a user cannot be their own friend. Return True if the edge was new.
        """
        if a == b:
            raise ValueError("a user cannot befriend themselves")
        if a not in self._adj:
            raise KeyError(f"unknown user {a}")
        if b not in self._adj:
            raise KeyError(f"unknown user {b}")
        if b in self._adj[a]:
            return False
        self._adj[a].add(b)
        self._adj[b].add(a)
        return True

    def remove_friendship(self, a: int, b: int) -> bool:
        """Delete the friendship between ``a`` and ``b``. Return True if removed."""
        if a not in self._adj or b not in self._adj:
            return False
        if b not in self._adj[a]:
            return False
        self._adj[a].discard(b)
        self._adj[b].discard(a)
        return True

    def are_friends(self, a: int, b: int) -> bool:
        return a in self._adj and b in self._adj[a]

    def neighbours(self, user_id: int) -> Set[int]:
        """Return a *copy* of the direct friends of ``user_id`` (distance 1)."""
        if user_id not in self._adj:
            raise KeyError(f"unknown user {user_id}")
        return set(self._adj[user_id])

    def degree(self, user_id: int) -> int:
        if user_id not in self._adj:
            raise KeyError(f"unknown user {user_id}")
        return len(self._adj[user_id])

    def edge_count(self) -> int:
        """Number of undirected friendships. O(N)."""
        return sum(len(friends) for friends in self._adj.values()) // 2

    def edges(self) -> Iterator[Tuple[int, int]]:
        """Yield each undirected edge once, as a sorted (low, high) pair."""
        for a, friends in self._adj.items():
            for b in friends:
                if a < b:
                    yield (a, b)

    # --- Breadth-First Search (Lecture 8, LAB 6 Ex.2/Ex.3) --------------------

    def bfs_levels(self, source: int) -> Dict[int, int]:
        """Return ``{reachable_user: distance_from_source}`` using BFS.

        The distance is the number of friendship hops. ``source`` itself is at
        distance 0. Implements the classic queue-based BFS of Lecture 8: every
        node and edge is examined at most once, hence **O(N + E)**.
        """
        if source not in self._adj:
            raise KeyError(f"unknown user {source}")
        distance: Dict[int, int] = {source: 0}
        queue: deque[int] = deque([source])
        while queue:
            current = queue.popleft()
            for friend in self._adj[current]:
                if friend not in distance:
                    distance[friend] = distance[current] + 1
                    queue.append(friend)
        return distance

    def nodes_at_distance(self, source: int, k: int) -> Set[int]:
        """Return every user exactly ``k`` friendship hops away from source.

        ``k = 1`` gives the direct friends; ``k = 2`` gives the "friends of
        friends" used by the Social Discovery feature (slide 6). O(N + E).
        """
        if k < 0:
            raise ValueError("distance k must be >= 0")
        return {u for u, d in self.bfs_levels(source).items() if d == k}

    def friends_within_k_hops(self, source: int, k: int) -> Set[int]:
        """Return every user reachable in 1..k hops (excluding the source).

        Reference: LAB 6 Ex.3 ``friends_within_k_hops``. O(N + E).
        """
        if k < 0:
            raise ValueError("distance k must be >= 0")
        return {u for u, d in self.bfs_levels(source).items() if 1 <= d <= k}

    def shortest_path_length(self, source: int, target: int) -> Optional[int]:
        """Return the number of hops on a shortest path, or None if unreachable.

        Unweighted shortest path = BFS depth (Lecture 8). O(N + E).
        """
        if target not in self._adj:
            raise KeyError(f"unknown user {target}")
        return self.bfs_levels(source).get(target)

    def shortest_path(self, source: int, target: int) -> Optional[List[int]]:
        """Return one shortest friendship path ``[source, ..., target]``.

        BFS while remembering each node's predecessor, then walk the parents
        back. Returns None when ``target`` is unreachable. O(N + E).
        """
        if source not in self._adj:
            raise KeyError(f"unknown user {source}")
        if target not in self._adj:
            raise KeyError(f"unknown user {target}")
        if source == target:
            return [source]
        parent: Dict[int, int] = {source: source}
        queue: deque[int] = deque([source])
        while queue:
            current = queue.popleft()
            for friend in self._adj[current]:
                if friend not in parent:
                    parent[friend] = current
                    if friend == target:
                        return self._rebuild_path(parent, source, target)
                    queue.append(friend)
        return None

    @staticmethod
    def _rebuild_path(parent: Dict[int, int], source: int, target: int) -> List[int]:
        path = [target]
        while path[-1] != source:
            path.append(parent[path[-1]])
        path.reverse()
        return path

    # --- Depth-First Search (Lecture 8, LAB 6 Ex.2) ---------------------------

    def dfs_preorder(self, source: int) -> List[int]:
        """Return the user_ids reachable from ``source`` in DFS pre-order.

        Iterative DFS with an explicit stack (Lecture 6 advises converting the
        recursion to a loop to avoid deep call stacks on large graphs). To make
        the order deterministic we push neighbours in descending order so the
        smallest id is explored first. O(N + E).
        """
        if source not in self._adj:
            raise KeyError(f"unknown user {source}")
        visited: Set[int] = set()
        order: List[int] = []
        stack: List[int] = [source]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            order.append(current)
            for friend in sorted(self._adj[current], reverse=True):
                if friend not in visited:
                    stack.append(friend)
        return order

    # --- Connected components = community detection (Lecture 8) ---------------

    def connected_components(self) -> List[List[int]]:
        """Partition the users into connected components (one BFS per component).

        Each component is a maximal set of users mutually reachable through
        friendships — the simplest notion of a "community" in the ASNAP brief.
        Components and their members are returned sorted for reproducibility.
        Total cost is O(N + E): every node/edge is visited once across all BFS
        runs.
        """
        seen: Set[int] = set()
        components: List[List[int]] = []
        for start in self._adj:
            if start in seen:
                continue
            component = sorted(self.bfs_levels(start).keys())
            seen.update(component)
            components.append(component)
        components.sort(key=lambda comp: (comp[0] if comp else -1))
        return components

    # --- Adjacency matrix view (LAB 6 Ex.1: matrix vs list) -------------------

    def to_adjacency_matrix(
        self, order: Optional[Iterable[int]] = None
    ) -> Tuple[List[int], List[List[int]]]:
        """Return ``(ids, matrix)`` where ``matrix[i][j] == 1`` iff ``ids[i]`` and
        ``ids[j]`` are friends.

        This is the dense O(N^2) representation contrasted with the adjacency
        list in LAB 6. Useful to reason about density (a complete graph fills
        the matrix with ones, an empty graph leaves it all zeros).
        """
        ids = sorted(self._adj.keys()) if order is None else list(order)
        index = {uid: i for i, uid in enumerate(ids)}
        n = len(ids)
        matrix = [[0] * n for _ in range(n)]
        for a, friends in self._adj.items():
            if a not in index:
                continue
            for b in friends:
                if b in index:
                    matrix[index[a]][index[b]] = 1
        return ids, matrix

    # --- Bulk construction helper --------------------------------------------

    def add_users(self, user_ids: Iterable[int]) -> None:
        for uid in user_ids:
            self.add_user(uid)

    def __len__(self) -> int:
        return len(self._adj)

    def __contains__(self, user_id: object) -> bool:
        return isinstance(user_id, int) and user_id in self._adj
