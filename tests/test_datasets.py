"""Unit tests for backend.datasets (graph generators of varying sizes)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.datasets import (
    complete_graph,
    empty_graph,
    path_graph,
    random_social_graph,
    star_graph,
)


class DatasetTest(unittest.TestCase):
    def test_empty(self):
        g = empty_graph(5)
        self.assertEqual(g.user_count(), 5)
        self.assertEqual(g.edge_count(), 0)

    def test_path(self):
        g = path_graph(4)
        self.assertEqual(g.edge_count(), 3)
        self.assertTrue(g.are_friends(1, 2))
        self.assertFalse(g.are_friends(1, 3))

    def test_star(self):
        g = star_graph(5)
        self.assertEqual(g.degree(1), 4)       # centre
        self.assertEqual(g.degree(2), 1)       # leaf

    def test_complete(self):
        g = complete_graph(4)
        self.assertEqual(g.edge_count(), 6)    # n(n-1)/2

    def test_random_is_reproducible(self):
        g1 = random_social_graph(20, 0.2, seed=123)
        g2 = random_social_graph(20, 0.2, seed=123)
        self.assertEqual(list(g1.edges()), list(g2.edges()))

    def test_random_density_bounds(self):
        g0 = random_social_graph(10, 0.0, seed=1)
        gf = random_social_graph(10, 1.0, seed=1)
        self.assertEqual(g0.edge_count(), 0)
        self.assertEqual(gf.edge_count(), 45)  # complete

    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            random_social_graph(5, 1.5)


if __name__ == "__main__":
    unittest.main()
