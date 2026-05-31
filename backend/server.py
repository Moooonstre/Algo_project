"""HTTP server for the Social Gate login feature.

Endpoints
---------
    POST /api/register         -> create a new user
    POST /api/login            -> issue a session cookie
    POST /api/logout           -> revoke the current session
    GET  /api/me               -> return the current user
    GET  /                     -> static frontend
    GET  /<path>               -> static frontend asset

The server uses only the Python standard library (``http.server``,
``json``, ``http.cookies``); the course does not introduce any web framework
so we keep the dependency surface to zero.

Sessions are kept in a process-local hash map (``backend.auth.SessionStore``)
and exposed to the browser as an HttpOnly cookie called ``session``.
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .auth import SessionStore
from .feed import proximity_score, rank_timeline
from .filters import (
    filter_by_friend_like_threshold,
    filter_recommendations_by_mutual,
)
from .hard_problems import detect_communities, find_fast_coverage
from .posts import PostError, PostStore
from .recommendation import recommend_friends
from .social_store import FriendshipError, SocialStore
from .user_store import (
    DuplicateUserError,
    UserStore,
    ValidationError,
)


SESSION_COOKIE = "session"
DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "users.json"
DEFAULT_FRIENDS_DB = (
    Path(__file__).resolve().parent.parent / "data" / "friends.json"
)
DEFAULT_POSTS_DB = (
    Path(__file__).resolve().parent.parent / "data" / "posts.json"
)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def make_handler(
    user_store: UserStore,
    sessions: SessionStore,
    social: SocialStore,
    posts: PostStore,
):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SocialGateLogin/0.1"

        # --- helpers ------------------------------------------------------

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValidationError("body is not valid JSON") from exc
            if not isinstance(payload, dict):
                raise ValidationError("body must be a JSON object")
            return payload

        def _send_json(
            self,
            status: HTTPStatus,
            payload: dict,
            extra_headers: list[tuple[str, str]] | None = None,
        ) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for name, value in extra_headers or []:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _current_user(self):
            cookie_header = self.headers.get("Cookie", "")
            if not cookie_header:
                return None, None
            cookies = SimpleCookie()
            cookies.load(cookie_header)
            morsel = cookies.get(SESSION_COOKIE)
            if morsel is None:
                return None, None
            token = morsel.value
            user_id = sessions.get(token)
            if user_id is None:
                return None, None
            return token, user_store.find_by_id(user_id)

        def _query_int(self, name: str, default: int) -> int:
            """Read an integer query-string parameter, falling back to default."""
            values = parse_qs(urlparse(self.path).query).get(name)
            if not values:
                return default
            try:
                return int(values[0])
            except (TypeError, ValueError):
                return default

        def _set_session_cookie(self, token: str) -> tuple[str, str]:
            return (
                "Set-Cookie",
                f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict",
            )

        def _clear_session_cookie(self) -> tuple[str, str]:
            return (
                "Set-Cookie",
                f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; "
                "Max-Age=0",
            )

        # --- routing ------------------------------------------------------

        def do_POST(self) -> None:  # noqa: N802 - http.server convention
            path = urlparse(self.path).path
            try:
                if path == "/api/register":
                    self._handle_register()
                elif path == "/api/login":
                    self._handle_login()
                elif path == "/api/logout":
                    self._handle_logout()
                elif path == "/api/friends/add":
                    self._handle_add_friend()
                elif path == "/api/friends/remove":
                    self._handle_remove_friend()
                elif path == "/api/posts":
                    self._handle_create_post()
                elif path == "/api/posts/like":
                    self._handle_like_post()
                elif path == "/api/posts/unlike":
                    self._handle_unlike_post()
                else:
                    self._send_json(
                        HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"}
                    )
            except ValidationError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except FriendshipError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except PostError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except DuplicateUserError as exc:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
            except Exception:
                logging.exception("unhandled error on %s", path)
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "internal error"},
                )

        def do_GET(self) -> None:  # noqa: N802 - http.server convention
            path = urlparse(self.path).path
            try:
                if path == "/api/me":
                    self._handle_me()
                elif path == "/api/friends":
                    self._handle_list_friends()
                elif path == "/api/recommendations":
                    self._handle_recommendations()
                elif path == "/api/timeline":
                    self._handle_timeline()
                elif path == "/api/communities":
                    self._handle_communities()
                elif path == "/api/influencers":
                    self._handle_influencers()
                else:
                    self._serve_static(path)
            except Exception:
                logging.exception("unhandled error on %s", path)
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "internal error"},
                )

        # --- endpoints ----------------------------------------------------

        def _handle_register(self) -> None:
            payload = self._read_json_body()
            user = user_store.register(payload)
            social.ensure_user(user.user_id)  # every user is a graph node
            token = sessions.create(user.user_id)
            self._send_json(
                HTTPStatus.CREATED,
                {"user": user.public_dict()},
                extra_headers=[self._set_session_cookie(token)],
            )

        def _handle_login(self) -> None:
            payload = self._read_json_body()
            identifier = payload.get("username") or payload.get("email")
            password = payload.get("password")
            if not isinstance(identifier, str) or not isinstance(password, str):
                raise ValidationError("username/email and password are required")
            user = user_store.authenticate(identifier, password)
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "invalid credentials"}
                )
                return
            token = sessions.create(user.user_id)
            self._send_json(
                HTTPStatus.OK,
                {"user": user.public_dict()},
                extra_headers=[self._set_session_cookie(token)],
            )

        def _handle_logout(self) -> None:
            token, _user = self._current_user()
            if token is not None:
                sessions.revoke(token)
            self._send_json(
                HTTPStatus.OK,
                {"ok": True},
                extra_headers=[self._clear_session_cookie()],
            )

        def _handle_me(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            self._send_json(HTTPStatus.OK, {"user": user.public_dict()})

        # --- friendships (Bloc A: social graph) ---------------------------

        def _require_friend_id(self, payload: dict) -> int:
            friend_id = payload.get("friend_id")
            if isinstance(friend_id, bool) or not isinstance(friend_id, int):
                raise ValidationError("friend_id (integer) is required")
            return friend_id

        def _handle_add_friend(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            payload = self._read_json_body()
            friend_id = self._require_friend_id(payload)
            created = social.add_friend(user.user_id, friend_id)
            self._send_json(
                HTTPStatus.OK,
                {"created": created, "friends": social.friends(user.user_id)},
            )

        def _handle_remove_friend(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            payload = self._read_json_body()
            friend_id = self._require_friend_id(payload)
            removed = social.remove_friend(user.user_id, friend_id)
            self._send_json(
                HTTPStatus.OK,
                {"removed": removed, "friends": social.friends(user.user_id)},
            )

        def _handle_list_friends(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            self._send_json(
                HTTPStatus.OK, {"friends": social.friends(user.user_id)}
            )

        # --- Social Discovery (Bloc B: friend recommendation) -------------

        def _handle_recommendations(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            # friends of friends, ranked by mutual-friend count (LAB6 Ex.3 +
            # LAB2 Ex.2). Enrich each suggestion with the public profile.
            suggestions = recommend_friends(social.graph, user.user_id, limit=20)
            # Gate Settings: optional mutual-friends threshold (slide 5).
            min_mutual = self._query_int("min_mutual", 0)
            suggestions = filter_recommendations_by_mutual(suggestions, min_mutual)
            payload = []
            for s in suggestions:
                profile = user_store.find_by_id(s.user_id)
                entry = {"user_id": s.user_id, "mutual_friends": s.mutual_friends}
                if profile is not None:
                    pub = profile.public_dict()
                    entry["username"] = pub["username"]
                    entry["first_name"] = pub["first_name"]
                    entry["last_name"] = pub["last_name"]
                payload.append(entry)
            self._send_json(HTTPStatus.OK, {"recommendations": payload})

        # --- Gate Timeline (Bloc C: posts + proximity score + MergeSort) --

        def _handle_create_post(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            payload = self._read_json_body()
            content = payload.get("content")
            post = posts.create_post(user.user_id, content)
            self._send_json(HTTPStatus.CREATED, {"post": post.public_dict()})

        def _require_post_id(self, payload: dict) -> int:
            post_id = payload.get("post_id")
            if isinstance(post_id, bool) or not isinstance(post_id, int):
                raise PostError("post_id (integer) is required")
            return post_id

        def _handle_like_post(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            payload = self._read_json_body()
            post_id = self._require_post_id(payload)
            created = posts.like_post(post_id, user.user_id)
            self._send_json(HTTPStatus.OK, {"liked": created})

        def _handle_unlike_post(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            payload = self._read_json_body()
            post_id = self._require_post_id(payload)
            removed = posts.unlike_post(post_id, user.user_id)
            self._send_json(HTTPStatus.OK, {"unliked": removed})

        def _handle_timeline(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            # Score-sorted feed: all posts ranked by proximity score for this
            # viewer (project slide 6), ordered with our MergeSort (LAB4/L9).
            ranked = rank_timeline(posts.all_posts(), user.user_id, social.graph)
            # Gate Settings: optional confidence threshold = minimum number of
            # likes coming from the viewer's friends (slide 5).
            min_friend_likes = self._query_int("min_friend_likes", 0)
            ranked = filter_by_friend_like_threshold(
                ranked, user.user_id, social.graph, min_friend_likes
            )
            payload = []
            for post, score in ranked:
                author = user_store.find_by_id(post.author_id)
                entry = post.public_dict()
                entry["score"] = score
                entry["liked_by_me"] = user.user_id in post.likes
                if author is not None:
                    pub = author.public_dict()
                    entry["author_username"] = pub["username"]
                    entry["author_name"] = pub["first_name"] + " " + pub["last_name"]
                payload.append(entry)
            self._send_json(HTTPStatus.OK, {"timeline": payload})

        # --- ASNAP intelligence demo (Bloc E algorithms over the API) -----

        def _label(self, user_id: int) -> str:
            u = user_store.find_by_id(user_id)
            return u.username if u is not None else str(user_id)

        def _handle_communities(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            # Connected components = communities (Lecture 8).
            comps = detect_communities(social.graph)
            payload = [
                {"members": comp, "usernames": [self._label(u) for u in comp]}
                for comp in comps
            ]
            self._send_json(HTTPStatus.OK, {"communities": payload})

        def _handle_influencers(self) -> None:
            _token, user = self._current_user()
            if user is None:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED, {"error": "not authenticated"}
                )
                return
            # Greedy minimum dominating set (LAB 9 Ex.1): a small set of users
            # that reaches everyone in 1 hop.
            size, selected = find_fast_coverage(social.graph)
            self._send_json(
                HTTPStatus.OK,
                {
                    "size": size,
                    "influencers": selected,
                    "usernames": [self._label(u) for u in selected],
                },
            )

        # --- static files -------------------------------------------------

        def _serve_static(self, path: str) -> None:
            relative = path.lstrip("/") or "index.html"
            target = (FRONTEND_DIR / relative).resolve()
            try:
                target.relative_to(FRONTEND_DIR.resolve())
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if target.is_dir():
                target = target / "index.html"
            if not target.exists() or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            ctype, _ = mimetypes.guess_type(str(target))
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type", ctype or "application/octet-stream"
            )
            self.send_header("Content-Length", str(target.stat().st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with target.open("rb") as f:
                self.wfile.write(f.read())

        # --- noisy log silencer ------------------------------------------

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            logging.info("%s - %s", self.client_address[0], format % args)

    return Handler


def build_server(
    host: str,
    port: int,
    db_path: Path,
    friends_db_path: Path | None = None,
    posts_db_path: Path | None = None,
) -> tuple[ThreadingHTTPServer, UserStore]:
    user_store = UserStore(db_path)
    sessions = SessionStore()
    social = SocialStore(friends_db_path or DEFAULT_FRIENDS_DB)
    # Seed the graph with every existing user so they are all nodes.
    social.sync_users(u.user_id for u in user_store.all_users())
    posts = PostStore(posts_db_path or DEFAULT_POSTS_DB)
    handler_cls = make_handler(user_store, sessions, social, posts)
    httpd = ThreadingHTTPServer((host, port), handler_cls)
    return httpd, user_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Social Gate login server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help="path to the JSON file used to persist users",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    db_path = Path(args.db)
    httpd, store = build_server(args.host, args.port, db_path)
    logging.info(
        "Social Gate login server listening on http://%s:%d (users=%d, db=%s)",
        args.host,
        args.port,
        store.size(),
        db_path,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("shutting down")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
