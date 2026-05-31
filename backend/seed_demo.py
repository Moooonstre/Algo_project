"""Seed the site with realistic demo data (course-aligned, stdlib only).

Populates the JSON stores used by the server so the site shows something
meaningful on first open: a handful of users, friendships that form two
communities, and posts liked across friend / stranger boundaries (to make the
proximity score and the MergeSort ranking visible).

Run from the repository root:

    python -m backend.seed_demo            # seed into data/ (skips if non-empty)
    python -m backend.seed_demo --reset    # wipe data/ first, then seed

All demo accounts share the password ``password1``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .posts import PostStore
from .social_store import SocialStore
from .user_store import UserStore

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_DB = DATA_DIR / "users.json"
FRIENDS_DB = DATA_DIR / "friends.json"
POSTS_DB = DATA_DIR / "posts.json"

DEMO_PASSWORD = "password1"

# (username, first_name, last_name)
DEMO_USERS = [
    ("alice", "Alice", "Martin"),
    ("bob", "Bob", "Bernard"),
    ("carol", "Carol", "Petit"),
    ("dan", "Dan", "Durand"),
    ("erin", "Erin", "Robert"),
    ("frank", "Frank", "Moreau"),
    ("grace", "Grace", "Laurent"),
    ("heidi", "Heidi", "Simon"),
]

# friendships by username — two clusters + a bridge (alice-erin)
DEMO_FRIENDSHIPS = [
    ("alice", "bob"),
    ("alice", "carol"),
    ("bob", "carol"),
    ("bob", "dan"),
    ("carol", "dan"),
    ("erin", "frank"),
    ("erin", "grace"),
    ("frank", "grace"),
    ("grace", "heidi"),
    ("alice", "erin"),  # bridge between the two clusters
]

# posts: (author, content)
DEMO_POSTS = [
    ("dan", "Premier jour de stage, hâte de commencer ! 🚀"),
    ("carol", "Quelqu'un pour réviser les graphes ce week-end ?"),
    ("frank", "Mon nouveau setup est enfin prêt 💻"),
    ("alice", "Sortie vélo ce matin, vue magnifique 🚴"),
    ("heidi", "Recette de cookies testée et approuvée 🍪"),
]

# likes: (post_index, liker_username)
DEMO_LIKES = [
    (0, "alice"), (0, "bob"), (0, "carol"), (0, "heidi"),
    (1, "alice"), (1, "bob"), (1, "dan"),
    (2, "erin"), (2, "grace"),
    (3, "bob"), (3, "carol"), (3, "erin"),
    (4, "grace"), (4, "frank"),
]


def _reset() -> None:
    for path in (USERS_DB, FRIENDS_DB, POSTS_DB):
        if path.exists():
            path.unlink()


def seed() -> None:
    users = UserStore(USERS_DB)
    if users.size() > 0:
        print(
            f"data already contains {users.size()} user(s); "
            "use --reset to wipe and reseed."
        )
        return
    social = SocialStore(FRIENDS_DB)
    posts = PostStore(POSTS_DB)

    name_to_id: dict[str, int] = {}
    for username, first, last in DEMO_USERS:
        u = users.register(
            {
                "username": username,
                "email": f"{username}@socialgate.fr",
                "first_name": first,
                "last_name": last,
                "birth_date": "2003-01-01",
                "password": DEMO_PASSWORD,
            }
        )
        social.ensure_user(u.user_id)
        name_to_id[username] = u.user_id

    for a, b in DEMO_FRIENDSHIPS:
        social.add_friend(name_to_id[a], name_to_id[b])

    created = []
    for author, content in DEMO_POSTS:
        created.append(posts.create_post(name_to_id[author], content))

    for post_idx, liker in DEMO_LIKES:
        posts.like_post(created[post_idx].post_id, name_to_id[liker])

    print(
        f"Seeded {len(DEMO_USERS)} users, {len(DEMO_FRIENDSHIPS)} friendships, "
        f"{len(DEMO_POSTS)} posts, {len(DEMO_LIKES)} likes."
    )
    print(f"Login with any username above and password '{DEMO_PASSWORD}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Social Gate demo data")
    parser.add_argument(
        "--reset", action="store_true", help="wipe data/ before seeding"
    )
    args = parser.parse_args()
    if args.reset:
        _reset()
    seed()


if __name__ == "__main__":
    main()
