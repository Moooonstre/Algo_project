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
from urllib.parse import urlparse

from .auth import SessionStore
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
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def make_handler(
    user_store: UserStore, sessions: SessionStore, social: SocialStore
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
                else:
                    self._send_json(
                        HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"}
                    )
            except ValidationError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except FriendshipError as exc:
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
    host: str, port: int, db_path: Path, friends_db_path: Path | None = None
) -> tuple[ThreadingHTTPServer, UserStore]:
    user_store = UserStore(db_path)
    sessions = SessionStore()
    social = SocialStore(friends_db_path or DEFAULT_FRIENDS_DB)
    # Seed the graph with every existing user so they are all nodes.
    social.sync_users(u.user_id for u in user_store.all_users())
    handler_cls = make_handler(user_store, sessions, social)
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
