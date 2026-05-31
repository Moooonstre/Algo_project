"""Unit tests for backend.graph.SocialGraph.

Covers the edge cases the labs insist on (LAB 6 traversals, plus the empty /
complete / single-node graphs raised in LAB 9 and LAB 10).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.graph import SocialGraph


def build_graph(n, edges):
    g = SocialGraph()
    g.add_users(range(1, n + 1))
    for a, b in edges:
        g.add_friendship(a, b)
    return g


class GraphBasicsTest(unittest.TestCase):
    def test_empty_graph(self):
        g = SocialGraph()
        self.assertEqual(g.user_count(), 0)
        self.assertEqual(g.edge_count(), 0)
        self.assertEqual(g.connected_components(), [])

    def test_add_user_idempotent(self):
        g = SocialGraph()
        self.assertTrue(g.add_user(1))
        self.assertFalse(g.add_user(1))
        self.assertEqual(g.user_count(), 1)

    def test_add_friendship_is_symmetric(self):
        g = build_graph(2, [(1, 2)])
        self.assertTrue(g.are_friends(1, 2))
        self.assertTrue(g.are_friends(2, 1))
        self.assertEqual(g.degree(1), 1)
        self.assertEqual(g.edge_count(), 1)

    def test_add_friendship_duplicate_returns_false(self):
        g = build_graph(2, [(1, 2)])
        self.assertFalse(g.add_friendship(1, 2))
        self.assertEqual(g.edge_count(), 1)

    def test_self_loop_rejected(self):
        g = build_graph(1, [])
        with self.assertRaises(ValueError):
            g.add_friendship(1, 1)

    def test_friendship_unknown_user_raises(self):
        g = build_graph(2, [])
        with self.assertRaises(KeyError):
            g.add_friendship(1, 99)

    def test_remove_friendship(self):
        g = build_graph(2, [(1, 2)])
        self.assertTrue(g.remove_friendship(1, 2))
        self.assertFalse(g.are_friends(1, 2))
        self.assertFalse(g.remove_friendship(1, 2))

    def test_remove_user_clears_edges(self):
        g = build_graph(3, [(1, 2), (2, 3)])
        self.assertTrue(g.remove_user(2))
        self.assertFalse(g.has_user(2))
        self.assertEqual(g.degree(1), 0)
        self.assertEqual(g.degree(3), 0)
        self.assertEqual(g.edge_count(), 0)


class BfsTest(unittest.TestCase):
    def setUp(self):
        # 1-2-3-4 chain plus an isolated triangle 5-6-7, and lone node 8.
        self.g = build_graph(
            8, [(1, 2), (2, 3), (3, 4), (5, 6), (6, 7), (5, 7)]
        )

    def test_bfs_levels(self):
        levels = self.g.bfs_levels(1)
        self.assertEqual(levels, {1: 0, 2: 1, 3: 2, 4: 3})

    def test_nodes_at_distance_two_are_friends_of_friends(self):
        self.assertEqual(self.g.nodes_at_distance(1, 2), {3})

    def test_friends_within_k_hops(self):
        self.assertEqual(self.g.friends_within_k_hops(1, 2), {2, 3})

    def test_shortest_path_length(self):
        self.assertEqual(self.g.shortest_path_length(1, 4), 3)
        self.assertIsNone(self.g.shortest_path_length(1, 8))

    def test_shortest_path_route(self):
        self.assertEqual(self.g.shortest_path(1, 4), [1, 2, 3, 4])
        self.assertEqual(self.g.shortest_path(1, 1), [1])
        self.assertIsNone(self.g.shortest_path(1, 5))

    def test_negative_distance_rejected(self):
        with self.assertRaises(ValueError):
            self.g.nodes_at_distance(1, -1)


class DfsAndComponentsTest(unittest.TestCase):
    def test_dfs_preorder_deterministic(self):
        g = build_graph(4, [(1, 2), (1, 3), (2, 4)])
        # From 1: visit 1, then smallest neighbour 2, then its neighbour 4,
        # backtrack to 3.
        self.assertEqual(g.dfs_preorder(1), [1, 2, 4, 3])

    def test_connected_components(self):
        g = build_graph(8, [(1, 2), (2, 3), (3, 4), (5, 6), (6, 7), (5, 7)])
        self.assertEqual(
            g.connected_components(), [[1, 2, 3, 4], [5, 6, 7], [8]]
        )

    def test_components_of_empty_edges(self):
        g = build_graph(3, [])
        self.assertEqual(g.connected_components(), [[1], [2], [3]])


class AdjacencyMatrixTest(unittest.TestCase):
    def test_matrix_of_triangle(self):
        g = build_graph(3, [(1, 2), (2, 3), (1, 3)])
        ids, matrix = g.to_adjacency_matrix()
        self.assertEqual(ids, [1, 2, 3])
        self.assertEqual(
            matrix,
            [[0, 1, 1], [1, 0, 1], [1, 1, 0]],
        )

    def test_matrix_of_empty_graph_is_all_zeros(self):
        g = build_graph(3, [])
        _, matrix = g.to_adjacency_matrix()
        self.assertTrue(all(cell == 0 for row in matrix for cell in row))

    def test_complete_graph_matrix_is_all_ones_off_diagonal(self):
        g = build_graph(4, [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
        ids, matrix = g.to_adjacency_matrix()
        for i in range(len(ids)):
            for j in range(len(ids)):
                expected = 0 if i == j else 1
                self.assertEqual(matrix[i][j], expected)


if __name__ == "__main__":
    unittest.main()
