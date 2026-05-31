"""Unit tests for backend.hard_problems (LAB 9 & LAB 10 exercises).

Includes the lab edge cases: empty graph, complete graph, no-edges graph,
budget=0, greedy-vs-exact counterexamples.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.graph import SocialGraph
from backend.hard_problems import (
    assign_labels,
    count_cross_edges,
    detect_communities,
    fast_alternative_strategy,
    find_balanced_partition_greedy,
    find_balanced_partition_local_search,
    find_fast_coverage,
    find_max_invitations_exact,
    find_max_invitations_greedy,
    find_min_labels,
    find_minimum_coverage,
    is_valid_coverage,
    is_valid_invitation,
    is_valid_labeling,
    is_within_budget,
    maximize_reach,
    maximize_reach_exact,
    maximize_reach_greedy,
)


def build_graph(nodes, edges):
    g = SocialGraph()
    g.add_users(nodes)
    for a, b in edges:
        g.add_friendship(a, b)
    return g


def star(n):
    # center 1 connected to 2..n
    return build_graph(range(1, n + 1), [(1, i) for i in range(2, n + 1)])


def complete(n):
    nodes = list(range(1, n + 1))
    edges = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]]
    return build_graph(nodes, edges)


class CommunityTest(unittest.TestCase):
    def test_components(self):
        g = build_graph([1, 2, 3, 4, 5], [(1, 2), (2, 3), (4, 5)])
        self.assertEqual(detect_communities(g), [[1, 2, 3], [4, 5]])


class DominatingSetTest(unittest.TestCase):
    def test_is_valid_coverage_star(self):
        g = star(5)
        self.assertTrue(is_valid_coverage([1], g))      # centre dominates all
        self.assertFalse(is_valid_coverage([2], g))     # leaf misses other leaves

    def test_minimum_coverage_star_is_one(self):
        g = star(5)
        size, sel = find_minimum_coverage(g)
        self.assertEqual(size, 1)
        self.assertEqual(sel, [1])

    def test_fast_coverage_valid_and_covers(self):
        g = build_graph([1, 2, 3, 4, 5, 6], [(1, 2), (2, 3), (4, 5), (5, 6)])
        size, sel = find_fast_coverage(g)
        self.assertTrue(is_valid_coverage(sel, g))

    def test_empty_graph(self):
        self.assertEqual(find_minimum_coverage(SocialGraph()), (0, []))


class ColoringTest(unittest.TestCase):
    def test_triangle_needs_three(self):
        g = complete(3)
        k, labeling = find_min_labels(g)
        self.assertEqual(k, 3)
        self.assertTrue(is_valid_labeling(labeling, g))

    def test_two_colours_fail_on_triangle(self):
        ok, _ = assign_labels(2, complete(3))
        self.assertFalse(ok)

    def test_no_edges_one_colour(self):
        g = build_graph([1, 2, 3], [])
        self.assertEqual(find_min_labels(g)[0], 1)

    def test_complete_k4_needs_four(self):
        self.assertEqual(find_min_labels(complete(4))[0], 4)

    def test_empty_graph_zero_colours(self):
        self.assertEqual(find_min_labels(SocialGraph()), (0, {}))


class KnapsackTest(unittest.TestCase):
    def test_exact_optimum(self):
        # items (cost, influence): (2,3)(3,4)(4,5)(5,6), budget 5 -> pick 0,1 = 7
        max_inf, sel = maximize_reach(5, [2, 3, 4, 5], [3, 4, 5, 6])
        self.assertEqual(max_inf, 7)
        self.assertEqual(sel, [0, 1])
        self.assertTrue(is_within_budget(sel, [2, 3, 4, 5], 5))

    def test_budget_zero(self):
        self.assertEqual(maximize_reach(0, [1, 2], [5, 6]), (0, []))

    def test_greedy_can_be_suboptimal(self):
        # exact picks items 1,2 (cost 8, inf 12); greedy by ratio picks 0 then 1
        costs, infs, budget = [3, 4, 4], [5, 6, 6], 8
        exact, _ = maximize_reach(budget, costs, infs)
        greedy, _ = fast_alternative_strategy(budget, costs, infs)
        self.assertEqual(exact, 12)
        self.assertLess(greedy, exact)

    def test_lab10_aliases_match(self):
        # LAB10 Ex.2 names delegate to the LAB9 Ex.3 implementations
        costs, reaches, budget = [2, 3, 4, 5], [3, 4, 5, 6], 5
        self.assertEqual(
            maximize_reach_exact(budget, costs, reaches),
            maximize_reach(budget, costs, reaches),
        )
        self.assertEqual(
            maximize_reach_greedy(budget, costs, reaches),
            fast_alternative_strategy(budget, costs, reaches),
        )


class IndependentSetTest(unittest.TestCase):
    def test_is_valid_invitation(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4)])
        self.assertTrue(is_valid_invitation([1, 3], g))
        self.assertFalse(is_valid_invitation([1, 2], g))

    def test_exact_path_of_four(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4)])
        size, sel = find_max_invitations_exact(g)
        self.assertEqual(size, 2)
        self.assertTrue(is_valid_invitation(sel, g))

    def test_triangle_max_is_one(self):
        self.assertEqual(find_max_invitations_exact(complete(3))[0], 1)

    def test_greedy_path_of_four(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4)])
        size, sel = find_max_invitations_greedy(g)
        self.assertEqual(size, 2)
        self.assertTrue(is_valid_invitation(sel, g))


class BalancedCutTest(unittest.TestCase):
    def test_count_cross_edges(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (3, 4), (2, 3)])
        self.assertEqual(count_cross_edges([1, 2], [3, 4], g), 1)

    def test_greedy_partition_is_balanced_and_valid(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (3, 4), (2, 3)])
        cross, a, b = find_balanced_partition_greedy(g)
        self.assertEqual(sorted(a + b), [1, 2, 3, 4])
        self.assertGreaterEqual(len(a), 2)  # 40% of 4 = ceil(1.6) = 2
        self.assertGreaterEqual(len(b), 2)
        self.assertEqual(cross, count_cross_edges(a, b, g))

    def test_local_search_finds_min_cut(self):
        g = build_graph([1, 2, 3, 4], [(1, 2), (3, 4), (2, 3)])
        cross, _, _ = find_balanced_partition_local_search(g, iterations=20, seed=1)
        self.assertEqual(cross, 1)  # best balanced cut separates the bridge only


if __name__ == "__main__":
    unittest.main()
