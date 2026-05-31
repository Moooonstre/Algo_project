"""Post store: posts and their likes, persisted to a JSON file.

A post is authored by a user (a graph node) and can be *liked* by other users.
The set of likers is what feeds the proximity-score ranking of the timeline
(see :mod:`backend.feed`). Persistence uses a single JSON file (``File`` type,
Lecture 3) — no SGBD, consistent with the rest of the project.

File format (``data/posts.json``)::

    {
      "next_id": 4,
      "posts": [
        {"post_id": 1, "author_id": 2, "content": "hello",
         "created_at": "2026-05-31T10:00:00Z", "likes": [3, 4]}
      ]
    }
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional


class PostError(ValueError):
    """Raised for invalid post operations (empty content, unknown post)."""


CONTENT_MAX_LEN = 500


@dataclass
class Post:
    post_id: int
    author_id: int
    content: str
    created_at: str
    likes: List[int] = field(default_factory=list)

    def public_dict(self, like_count: Optional[int] = None) -> dict:
        d = asdict(self)
        d["like_count"] = len(self.likes) if like_count is None else like_count
        return d


class PostStore:
    """In-memory posts keyed by post_id, persisted to JSON."""

    def __init__(self, db_path: str | os.PathLike) -> None:
        self._db_path = Path(db_path)
        self._lock = RLock()
        self._posts: Dict[int, Post] = {}
        self._next_id = 1
        self._load()

    # --- Commands -------------------------------------------------------------

    def create_post(self, author_id: int, content: str) -> Post:
        if not isinstance(content, str) or not content.strip():
            raise PostError("content must be a non-empty string")
        content = content.strip()
        if len(content) > CONTENT_MAX_LEN:
            raise PostError(f"content must be <= {CONTENT_MAX_LEN} characters")
        with self._lock:
            post = Post(
                post_id=self._next_id,
                author_id=author_id,
                content=content,
                created_at=datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                likes=[],
            )
            self._posts[post.post_id] = post
            self._next_id += 1
            self._save()
            return post

    def like_post(self, post_id: int, user_id: int) -> bool:
        """Register that ``user_id`` likes ``post_id``. Return True if new."""
        with self._lock:
            post = self._posts.get(post_id)
            if post is None:
                raise PostError(f"unknown post {post_id}")
            if user_id in post.likes:
                return False
            post.likes.append(user_id)
            self._save()
            return True

    def unlike_post(self, post_id: int, user_id: int) -> bool:
        with self._lock:
            post = self._posts.get(post_id)
            if post is None:
                raise PostError(f"unknown post {post_id}")
            if user_id not in post.likes:
                return False
            post.likes.remove(user_id)
            self._save()
            return True

    # --- Queries --------------------------------------------------------------

    def get_post(self, post_id: int) -> Optional[Post]:
        return self._posts.get(post_id)

    def all_posts(self) -> List[Post]:
        """Return every post (ordered by id)."""
        return [self._posts[pid] for pid in sorted(self._posts)]

    def posts_by_authors(self, author_ids) -> List[Post]:
        """Return posts whose author is in ``author_ids`` (a set/list)."""
        wanted = set(author_ids)
        return [p for p in self.all_posts() if p.author_id in wanted]

    def size(self) -> int:
        return len(self._posts)

    # --- Persistence (Lecture 3 — type File) ----------------------------------

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        with self._db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._next_id = int(data.get("next_id", 1))
        for record in data.get("posts", []):
            post = Post(
                post_id=int(record["post_id"]),
                author_id=int(record["author_id"]),
                content=record["content"],
                created_at=record["created_at"],
                likes=[int(x) for x in record.get("likes", [])],
            )
            self._posts[post.post_id] = post

    def _save(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "post_id": p.post_id,
                "author_id": p.author_id,
                "content": p.content,
                "created_at": p.created_at,
                "likes": list(p.likes),
            }
            for p in self.all_posts()
        ]
        tmp_path = self._db_path.with_suffix(self._db_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(
                {"next_id": self._next_id, "posts": records},
                f,
                indent=2,
                ensure_ascii=False,
            )
        os.replace(tmp_path, self._db_path)
