"""Binary Search Tree indexed by user_id.

Reference: LAB8 Exercise 1 - "Binary Search Trees - User Search & Friend-of-Friend
Suggestions". The structure follows the BST definition from Lecture 10 (slide 7):
for every node v, the left subtree contains keys <= v and the right subtree
contains keys strictly greater than v.

Average-case complexity for search/insert/delete is O(log n) for a balanced tree
and O(n) in the worst case (degenerate chain). See Lecture 10, slide 20.
"""

from __future__ import annotations

from typing import Callable, Iterator, Optional


class BSTNode:
    """A single node in the BST.

    Attributes match the convention of Lecture 10 (BST definition): one value,
    one left subtree, one right subtree. The "value" here is a key/value pair
    where the key is an integer user_id and the value is an opaque payload.
    """

    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key: int, value: object) -> None:
        self.key: int = key
        self.value: object = value
        self.left: Optional[BSTNode] = None
        self.right: Optional[BSTNode] = None


class BST:
    """Binary Search Tree keyed by integer user_id.

    Operations:
        insert(key, value)            : add a node, raise if key already exists
        search(key) -> value | None   : look up a value by key
        delete(key) -> bool           : remove a node by key
        in_order() -> iterator        : yield (key, value) sorted by key
        height() -> int               : tree height (-1 for the empty tree)
        size() -> int                 : number of nodes
    """

    def __init__(self) -> None:
        self._root: Optional[BSTNode] = None
        self._size: int = 0

    # --- Search (Lecture 10, slide 8) -----------------------------------------

    def search(self, key: int) -> Optional[object]:
        """Return the value associated with key, or None if absent.

        Iterative form (the recursion of Lecture 10 is tail-recursive, so we
        convert it to a loop as suggested in Lecture 6).
        """
        current = self._root
        while current is not None:
            if key == current.key:
                return current.value
            current = current.left if key < current.key else current.right
        return None

    def contains(self, key: int) -> bool:
        return self.search(key) is not None

    # --- Insertion at leaves (Lecture 10, slide 10) ---------------------------

    def insert(self, key: int, value: object) -> None:
        """Insert (key, value) at the appropriate leaf.

        Raises KeyError if the key already exists. Duplicate keys are rejected
        (same convention as the AVL insert in Lecture 10, slide 23).
        """
        if self._root is None:
            self._root = BSTNode(key, value)
            self._size += 1
            return

        current = self._root
        parent: Optional[BSTNode] = None
        while current is not None:
            if key == current.key:
                raise KeyError(f"key {key} already in BST")
            parent = current
            current = current.left if key < current.key else current.right

        new_node = BSTNode(key, value)
        assert parent is not None
        if key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node
        self._size += 1

    # --- Deletion (Lecture 10, slide 19) --------------------------------------

    def delete(self, key: int) -> bool:
        """Remove the node whose key matches. Return True if a node was removed.

        Uses the predecessor-replacement strategy: when the node to delete has
        two children, replace its value with the maximum of the left subtree
        and recursively delete that maximum.
        """
        self._root, removed = self._delete(self._root, key)
        if removed:
            self._size -= 1
        return removed

    def _delete(
        self, node: Optional[BSTNode], key: int
    ) -> tuple[Optional[BSTNode], bool]:
        if node is None:
            return None, False
        if key < node.key:
            node.left, removed = self._delete(node.left, key)
            return node, removed
        if key > node.key:
            node.right, removed = self._delete(node.right, key)
            return node, removed

        # key == node.key -> remove this node
        if node.left is None:
            return node.right, True
        if node.right is None:
            return node.left, True
        # Two children: replace with predecessor (max of left subtree).
        pred_node, new_left = self._extract_max(node.left)
        pred_node.left = new_left
        pred_node.right = node.right
        return pred_node, True

    def _extract_max(self, node: BSTNode) -> tuple[BSTNode, Optional[BSTNode]]:
        """Detach and return the maximum node of the subtree rooted at node.

        Also return the new root of the modified subtree (without the max).
        """
        if node.right is None:
            return node, node.left
        max_node, new_right = self._extract_max(node.right)
        node.right = new_right
        return max_node, node

    # --- Traversal (Lecture 7, slide 18) --------------------------------------

    def in_order(self) -> Iterator[tuple[int, object]]:
        """Yield (key, value) pairs in ascending key order.

        Iterative implementation using an explicit stack, as suggested in
        Lecture 6 to avoid recursion depth issues on large trees.
        """
        stack: list[BSTNode] = []
        current = self._root
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            yield current.key, current.value
            current = current.right

    def for_each(self, fn: Callable[[int, object], None]) -> None:
        """Apply fn(key, value) to every node in in-order."""
        for key, value in self.in_order():
            fn(key, value)

    # --- Metrics (Lecture 7, slide 19) ----------------------------------------

    def height(self) -> int:
        return self._height(self._root)

    def _height(self, node: Optional[BSTNode]) -> int:
        if node is None:
            return -1
        return 1 + max(self._height(node.left), self._height(node.right))

    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, int):
            return False
        return self.contains(key)
