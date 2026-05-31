"""ASNAP intelligence — the hard graph/optimization problems of LAB 9 & LAB 10.

Each function mirrors a lab exercise *exactly* (same name, same contract). They
are our own implementations (the ASNAP brief requires this) and operate on the
:class:`backend.graph.SocialGraph` (undirected friendship graph) or on plain
cost/value arrays for the knapsack.

LAB 9 — From Efficient Algorithms to Hard Problems
    Ex.1 Influencer Coverage  = minimum **dominating set**
    Ex.2 Conflict-Free Labeling = **graph colouring** (greedy backtracking)
    Ex.3 Ad Campaign          = 0/1 **knapsack** (dynamic programming) + greedy
LAB 10 — Backtracking, Optimization, DP & Greedy
    Ex.1 Event Invitation     = **maximum independent set** (backtracking+pruning)
    Ex.2 Viral Message        = 0/1 knapsack (same DP as LAB 9 Ex.3)
    Ex.3 Group Formation      = **balanced minimum cut** (greedy local search)

"Community detection" in the brief = connected components, already implemented
in :meth:`SocialGraph.connected_components` (Lecture 8); re-exported here as
``detect_communities`` for convenience.

Complexity notes follow each function; they match the lab's analysis questions.
"""

from __future__ import annotations

import random
from itertools import combinations
from math import ceil
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .graph import SocialGraph

# Brute force over all subsets is only feasible for small N (LAB 9: N <= 20).
BRUTE_FORCE_MAX_NODES = 22


# =============================================================================
# Community detection (Lecture 8) — connected components
# =============================================================================

def detect_communities(graph: SocialGraph) -> List[List[int]]:
    """Communities = connected components (Lecture 8). O(N + E)."""
    return graph.connected_components()


# =============================================================================
# LAB 9 Ex.1 — Influencer Coverage = minimum dominating set
# =============================================================================

def is_valid_coverage(selected_users: Sequence[int], graph: SocialGraph) -> bool:
    """True iff every node is selected or adjacent to a selected node.

    Dominating-set validity check (LAB 9 Ex.1). O(N + E): we mark the selected
    nodes and all their neighbours as covered, then verify every node is covered.
    """
    selected = set(selected_users)
    covered: Set[int] = set(selected)
    for u in selected:
        covered |= graph.neighbours(u)
    return all(u in covered for u in graph.users())


def find_minimum_coverage(graph: SocialGraph) -> Tuple[int, List[int]]:
    """Exact smallest dominating set by brute force over subsets (LAB 9 Ex.1).

    Tries every subset by increasing size and returns the first valid one, so it
    is guaranteed minimal. Exponential — feasible only for small graphs
    (N <= 20, as the lab states). O(2^N · (N + E)).
    """
    nodes = sorted(graph.users())
    n = len(nodes)
    if n == 0:
        return 0, []
    if n > BRUTE_FORCE_MAX_NODES:
        raise ValueError(
            f"brute force infeasible for N={n} (> {BRUTE_FORCE_MAX_NODES}); "
            "use find_fast_coverage"
        )
    for size in range(0, n + 1):
        for subset in combinations(nodes, size):
            if is_valid_coverage(subset, graph):
                return size, list(subset)
    return n, list(nodes)  # unreachable (the full set always covers)


def find_fast_coverage(graph: SocialGraph) -> Tuple[int, List[int]]:
    """Greedy dominating set: repeatedly pick the node covering the most still
    -uncovered nodes (LAB 9 Ex.1). Not always optimal, but scales. O(N·(N+E)).
    """
    uncovered: Set[int] = set(graph.users())
    selected: List[int] = []
    while uncovered:
        best_node = None
        best_gain = -1
        for u in sorted(graph.users()):
            # a node covers itself and its neighbours
            closed = {u} | graph.neighbours(u)
            gain = len(closed & uncovered)
            if gain > best_gain:
                best_gain, best_node = gain, u
        if best_node is None or best_gain <= 0:
            break
        selected.append(best_node)
        uncovered -= {best_node} | graph.neighbours(best_node)
    return len(selected), sorted(selected)


# =============================================================================
# LAB 9 Ex.2 — Conflict-Free Labeling = graph colouring
# =============================================================================

def is_valid_labeling(labeling: Dict[int, int], graph: SocialGraph) -> bool:
    """True iff every edge (u, v) has labeling[u] != labeling[v] (LAB 9 Ex.2).

    O(E).
    """
    for u, v in graph.edges():
        if labeling.get(u) == labeling.get(v):
            return False
    return True


def assign_labels(
    k: int, graph: SocialGraph
) -> Tuple[bool, Dict[int, int]]:
    """Try to colour the graph with at most ``k`` colours (greedy backtracking).

    Returns (success, labeling). Assigns colours 0..k-1 to nodes in id order,
    backtracking when stuck (LAB 9 Ex.2). Worst case O(k^N).
    """
    nodes = sorted(graph.users())
    if not nodes:
        return True, {}
    if k <= 0:
        return False, {}
    labeling: Dict[int, int] = {}

    def backtrack(i: int) -> bool:
        if i == len(nodes):
            return True
        node = nodes[i]
        used = {labeling[w] for w in graph.neighbours(node) if w in labeling}
        for color in range(k):
            if color not in used:
                labeling[node] = color
                if backtrack(i + 1):
                    return True
                del labeling[node]
        return False

    if backtrack(0):
        return True, dict(labeling)
    return False, {}


def find_min_labels(graph: SocialGraph) -> Tuple[int, Dict[int, int]]:
    """Smallest k for which assign_labels(k) succeeds = chromatic number.

    Tries k = 1, 2, 3, ... (LAB 9 Ex.2). Empty graph -> 0 colours; a graph with
    nodes but no edges -> 1 colour; complete graph K_n -> n colours.
    """
    nodes = sorted(graph.users())
    if not nodes:
        return 0, {}
    for k in range(1, len(nodes) + 1):
        ok, labeling = assign_labels(k, graph)
        if ok:
            return k, labeling
    return len(nodes), {n: i for i, n in enumerate(nodes)}


# =============================================================================
# LAB 9 Ex.3 / LAB 10 Ex.2 — Ad Campaign / Viral Message = 0/1 knapsack
# =============================================================================

def is_within_budget(
    selection: Sequence[int], costs: Sequence[int], budget: int
) -> bool:
    """True iff the total cost of the selected items is <= budget. O(N)."""
    return sum(costs[i] for i in selection) <= budget


def maximize_reach(
    budget: int, costs: Sequence[int], influences: Sequence[int]
) -> Tuple[int, List[int]]:
    """Exact 0/1 knapsack by dynamic programming (LAB 9 Ex.3 / LAB 10 Ex.2).

    Chooses a subset of items (users) with total cost <= budget maximising the
    sum of influence. Returns (max_influence, selected_indices). Runtime is
    O(N · budget) — pseudo-polynomial (not exponential in N) because the table is
    indexed by budget; this is why real-number costs would break it.
    """
    if budget < 0:
        raise ValueError("budget must be >= 0")
    n = len(costs)
    if n != len(influences):
        raise ValueError("costs and influences must have the same length")
    # dp[i][w] = best influence using the first i items with capacity w
    dp = [[0] * (budget + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cost_i, inf_i = costs[i - 1], influences[i - 1]
        for w in range(budget + 1):
            dp[i][w] = dp[i - 1][w]
            if cost_i <= w:
                cand = dp[i - 1][w - cost_i] + inf_i
                if cand > dp[i][w]:
                    dp[i][w] = cand
    # reconstruct the chosen items
    selected: List[int] = []
    w = budget
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(i - 1)
            w -= costs[i - 1]
    selected.reverse()
    return dp[n][budget], selected


def fast_alternative_strategy(
    budget: int, costs: Sequence[int], influences: Sequence[int]
) -> Tuple[int, List[int]]:
    """Greedy knapsack by influence/cost ratio (LAB 9 Ex.3 / LAB 10 Ex.2).

    Picks items by decreasing influence/cost ratio while they fit. Fast
    (O(N log N)) but not always optimal. Returns (total_influence, indices).
    """
    n = len(costs)
    order = sorted(
        range(n),
        key=lambda i: (influences[i] / costs[i]) if costs[i] > 0 else float("inf"),
        reverse=True,
    )
    total_inf = 0
    spent = 0
    selected: List[int] = []
    for i in order:
        if spent + costs[i] <= budget:
            selected.append(i)
            spent += costs[i]
            total_inf += influences[i]
    return total_inf, sorted(selected)


# =============================================================================
# LAB 10 Ex.1 — Event Invitation = maximum independent set
# =============================================================================

def is_valid_invitation(invited: Sequence[int], graph: SocialGraph) -> bool:
    """True iff no two invited users are connected by an edge (LAB 10 Ex.1).

    Independent-set validity check. O(k^2) where k = len(invited).
    """
    invited_list = list(invited)
    for a, b in combinations(invited_list, 2):
        if graph.are_friends(a, b):
            return False
    return True


def find_max_invitations_exact(graph: SocialGraph) -> Tuple[int, List[int]]:
    """Exact maximum independent set by backtracking with pruning (LAB 10 Ex.1).

    Branches include/exclude on each node; prunes when even adding all remaining
    nodes cannot beat the best set found so far. Feasible for small graphs
    (N <= 40, per the lab).
    """
    nodes = sorted(graph.users())
    n = len(nodes)
    best: List[int] = []

    def backtrack(i: int, current: List[int]) -> None:
        nonlocal best
        # prune: current + all remaining can't exceed the best found
        if len(current) + (n - i) <= len(best):
            return
        if i == n:
            if len(current) > len(best):
                best = list(current)
            return
        node = nodes[i]
        # include node if it conflicts with nobody already chosen
        if all(not graph.are_friends(node, c) for c in current):
            current.append(node)
            backtrack(i + 1, current)
            current.pop()
        # exclude node
        backtrack(i + 1, current)

    backtrack(0, [])
    return len(best), sorted(best)


def find_max_invitations_greedy(graph: SocialGraph) -> Tuple[int, List[int]]:
    """Greedy maximum independent set (LAB 10 Ex.1).

    Repeatedly pick the remaining node of smallest degree, add it to the set,
    then remove it and its neighbours. Not always optimal. O(N^2).
    """
    remaining: Set[int] = set(graph.users())
    invited: List[int] = []
    while remaining:
        node = min(
            remaining,
            key=lambda u: (
                sum(1 for w in graph.neighbours(u) if w in remaining),
                u,
            ),
        )
        invited.append(node)
        remaining.discard(node)
        remaining -= graph.neighbours(node)
    return len(invited), sorted(invited)


# =============================================================================
# LAB 10 Ex.3 — Group Formation = balanced minimum cut
# =============================================================================

def count_cross_edges(
    group_a: Sequence[int], group_b: Sequence[int], graph: SocialGraph
) -> int:
    """Number of edges with one endpoint in group_a and the other in group_b.

    LAB 10 Ex.3. O(E).
    """
    set_a, set_b = set(group_a), set(group_b)
    count = 0
    for u, v in graph.edges():
        if (u in set_a and v in set_b) or (u in set_b and v in set_a):
            count += 1
    return count


def _min_group_size(n: int) -> int:
    """Each group must contain at least 40% of all users (LAB 10 Ex.3)."""
    return ceil(0.4 * n)


def find_balanced_partition_greedy(
    graph: SocialGraph,
    initial: Optional[Tuple[Set[int], Set[int]]] = None,
) -> Tuple[int, List[int], List[int]]:
    """Greedy balanced minimum cut (LAB 10 Ex.3).

    Start from a balanced split (each group >= 40% of users), then repeatedly
    move a single user to the other group if it reduces the number of cross
    edges while keeping the balance. Stops at a local optimum.
    """
    nodes = sorted(graph.users())
    n = len(nodes)
    if n < 2:
        return 0, list(nodes), []
    min_size = _min_group_size(n)
    if initial is None:
        half = n // 2
        group_a: Set[int] = set(nodes[:half])
        group_b: Set[int] = set(nodes[half:])
    else:
        group_a, group_b = set(initial[0]), set(initial[1])

    def cross_delta_if_moved(node: int, own: Set[int], other: Set[int]) -> int:
        # reduction in cross edges if node moves from `own` to `other`
        din = sum(1 for w in graph.neighbours(node) if w in own and w != node)
        dout = sum(1 for w in graph.neighbours(node) if w in other)
        return din - dout

    improved = True
    while improved:
        improved = False
        for node in nodes:
            if node in group_a and len(group_a) - 1 >= min_size:
                if cross_delta_if_moved(node, group_a, group_b) > 0:
                    group_a.discard(node)
                    group_b.add(node)
                    improved = True
            elif node in group_b and len(group_b) - 1 >= min_size:
                if cross_delta_if_moved(node, group_b, group_a) > 0:
                    group_b.discard(node)
                    group_a.add(node)
                    improved = True
    return count_cross_edges(group_a, group_b, graph), sorted(group_a), sorted(group_b)


def find_balanced_partition_local_search(
    graph: SocialGraph, iterations: int = 10, seed: Optional[int] = None
) -> Tuple[int, List[int], List[int]]:
    """Run the greedy partition from several random balanced splits, keep the
    best (LAB 10 Ex.3). More iterations ⇒ better quality, more runtime.
    """
    nodes = sorted(graph.users())
    n = len(nodes)
    if n < 2:
        return 0, list(nodes), []
    rng = random.Random(seed)
    min_size = _min_group_size(n)
    best: Optional[Tuple[int, List[int], List[int]]] = None
    for _ in range(max(1, iterations)):
        shuffled = list(nodes)
        rng.shuffle(shuffled)
        # split point chosen so both sides respect the 40% balance
        low, high = min_size, n - min_size
        split = rng.randint(low, high) if low <= high else n // 2
        init = (set(shuffled[:split]), set(shuffled[split:]))
        cross, a, b = find_balanced_partition_greedy(graph, init)
        if best is None or cross < best[0]:
            best = (cross, a, b)
    assert best is not None
    return best
