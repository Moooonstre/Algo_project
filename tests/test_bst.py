"""Unit tests for backend.bst.BST.

The tests follow the edge-case checklist required by the labs (LAB8 final
section "Edge Cases to Consider").
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.bst import BST


class BSTBasicsTest(unittest.TestCase):
    def test_empty(self):
        tree = BST()
        self.assertEqual(tree.size(), 0)
        self.assertEqual(tree.height(), -1)
        self.assertIsNone(tree.search(42))
        self.assertFalse(tree.contains(42))
        self.assertFalse(tree.delete(42))
        self.assertEqual(list(tree.in_order()), [])

    def test_single_insert(self):
        tree = BST()
        tree.insert(10, "a")
        self.assertEqual(tree.size(), 1)
        self.assertEqual(tree.height(), 0)
        self.assertEqual(tree.search(10), "a")
        self.assertIn(10, tree)

    def test_duplicate_key_rejected(self):
        tree = BST()
        tree.insert(7, "first")
        with self.assertRaises(KeyError):
            tree.insert(7, "second")
        self.assertEqual(tree.search(7), "first")

    def test_in_order_is_sorted(self):
        tree = BST()
        keys = [5, 2, 8, 1, 3, 7, 9, 4, 6]
        for k in keys:
            tree.insert(k, f"v{k}")
        self.assertEqual([k for k, _ in tree.in_order()], sorted(keys))

    def test_search_random(self):
        tree = BST()
        for k in [50, 30, 70, 20, 40, 60, 80]:
            tree.insert(k, k * 2)
        self.assertEqual(tree.search(40), 80)
        self.assertEqual(tree.search(80), 160)
        self.assertIsNone(tree.search(999))


class BSTDeletionTest(unittest.TestCase):
    def setUp(self):
        self.tree = BST()
        for k in [50, 30, 70, 20, 40, 60, 80, 35, 45]:
            self.tree.insert(k, str(k))

    def test_delete_leaf(self):
        self.assertTrue(self.tree.delete(20))
        self.assertIsNone(self.tree.search(20))
        self.assertEqual(self.tree.size(), 8)

    def test_delete_node_with_one_child(self):
        self.tree.delete(20)  # 30 now has only right child (40)
        self.assertTrue(self.tree.delete(30))
        # 35 and 40, 45 must still be reachable
        for k in (35, 40, 45):
            self.assertEqual(self.tree.search(k), str(k))

    def test_delete_node_with_two_children(self):
        self.assertTrue(self.tree.delete(50))
        self.assertIsNone(self.tree.search(50))
        # In-order traversal must remain sorted after the deletion.
        keys = [k for k, _ in self.tree.in_order()]
        self.assertEqual(keys, sorted(keys))

    def test_delete_missing_key(self):
        self.assertFalse(self.tree.delete(123))
        self.assertEqual(self.tree.size(), 9)

    def test_delete_root_until_empty(self):
        keys_to_remove = [50, 30, 70, 20, 40, 60, 80, 35, 45]
        for k in keys_to_remove:
            self.assertTrue(self.tree.delete(k))
        self.assertEqual(self.tree.size(), 0)
        self.assertEqual(self.tree.height(), -1)


class BSTDegenerateChainTest(unittest.TestCase):
    """Inserting in increasing order produces a right-only chain (LAB8 Q2)."""

    def test_chain_height_equals_size_minus_one(self):
        tree = BST()
        for k in range(1, 11):
            tree.insert(k, k)
        self.assertEqual(tree.size(), 10)
        self.assertEqual(tree.height(), 9)


if __name__ == "__main__":
    unittest.main()
