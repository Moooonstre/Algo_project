/* Social Gate / ASNAP - frontend glue.
 *
 * Minimal vanilla JavaScript that wires the HTML pages to the JSON endpoints
 * exposed by backend/server.py. No frontend framework (none is covered by the
 * course). The "Gate Settings" thresholds are stored in localStorage and sent
 * as query parameters to the timeline / recommendations endpoints.
 */
(function () {
  "use strict";

  // --- HTTP helpers ---------------------------------------------------------

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      /* empty body is fine for some success responses */
    }
    return { res, data };
  }

  async function getJSON(url) {
    const res = await fetch(url, { credentials: "same-origin" });
    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      /* ignore */
    }
    return { res, data };
  }

  function showError(el, message) {
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  function clearError(el) {
    if (!el) return;
    el.hidden = true;
    el.textContent = "";
  }

  function setSubmitting(button, isSubmitting, idleLabel) {
    if (!button) return;
    button.disabled = isSubmitting;
    button.textContent = isSubmitting ? "…" : idleLabel;
  }

  // --- Gate Settings (thresholds persisted client-side) ---------------------

  function getSetting(key, fallback) {
    const v = window.localStorage.getItem(key);
    return v === null ? fallback : parseInt(v, 10);
  }

  function setSetting(key, value) {
    window.localStorage.setItem(key, String(value));
  }

  // --- Shared page chrome ---------------------------------------------------

  async function requireUser() {
    const { res, data } = await getJSON("/api/me");
    if (!res.ok) {
      window.location.replace("/login.html");
      return null;
    }
    return data.user;
  }

  function bindLogout() {
    const btn = document.getElementById("logout-btn");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        await fetch("/api/logout", { method: "POST", credentials: "same-origin" });
      } finally {
        window.location.replace("/login.html");
      }
    });
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  // --- Auth forms -----------------------------------------------------------

  function bindRegisterForm() {
    const form = document.getElementById("register-form");
    const errorEl = document.getElementById("register-error");
    const submit = document.getElementById("register-submit");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearError(errorEl);
      const data = Object.fromEntries(new FormData(form).entries());
      if (data.password !== data.password_confirm) {
        showError(errorEl, "Les mots de passe ne correspondent pas.");
        return;
      }
      delete data.password_confirm;
      setSubmitting(submit, true, "S'inscrire");
      try {
        const { res, data: payload } = await postJSON("/api/register", data);
        if (!res.ok) {
          showError(errorEl, payload.error || "Inscription impossible.");
          return;
        }
        window.location.replace("/home.html");
      } catch (err) {
        showError(errorEl, "Erreur réseau, réessayez.");
      } finally {
        setSubmitting(submit, false, "S'inscrire");
      }
    });
  }

  function bindLoginForm() {
    const form = document.getElementById("login-form");
    const errorEl = document.getElementById("login-error");
    const submit = document.getElementById("login-submit");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearError(errorEl);
      const data = Object.fromEntries(new FormData(form).entries());
      const body = {
        username: data.identifier,
        email: data.identifier,
        password: data.password,
      };
      setSubmitting(submit, true, "Se connecter");
      try {
        const { res, data: payload } = await postJSON("/api/login", body);
        if (!res.ok) {
          showError(errorEl, payload.error || "Connexion impossible.");
          return;
        }
        window.location.replace("/home.html");
      } catch (err) {
        showError(errorEl, "Erreur réseau, réessayez.");
      } finally {
        setSubmitting(submit, false, "Se connecter");
      }
    });
  }

  // --- Home hub -------------------------------------------------------------

  async function bootHomePage() {
    const user = await requireUser();
    if (!user) return;
    document.getElementById("display-name").textContent =
      user.first_name || user.username;
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    set("p-username", user.username);
    set("p-email", user.email);
    set("p-fullname", `${user.first_name} ${user.last_name}`.trim());
    set("p-birth", user.birth_date);
    set("p-created", user.created_at);

    // ASNAP intelligence preview: communities + influencers
    const { data: comm } = await getJSON("/api/communities");
    const { data: infl } = await getJSON("/api/influencers");
    const intel = document.getElementById("intel");
    if (intel) {
      const nbComm = (comm.communities || []).length;
      const influencers = (infl.usernames || []).join(", ") || "—";
      intel.innerHTML =
        `<li><strong>${nbComm}</strong> communauté(s) détectée(s) ` +
        `(composantes connexes, BFS)</li>` +
        `<li>Ensemble d'influenceurs minimal (dominating set glouton) : ` +
        `<strong>${esc(influencers)}</strong></li>`;
    }
    bindLogout();
  }

  // --- Gate Timeline --------------------------------------------------------

  async function bootTimelinePage() {
    const user = await requireUser();
    if (!user) return;
    bindLogout();

    const feedEl = document.getElementById("feed");
    const minLikes = getSetting("sg_min_friend_likes", 0);
    const badge = document.getElementById("threshold-badge");
    if (badge) {
      badge.textContent =
        minLikes > 0 ? `filtre actif : ≥ ${minLikes} like(s) d'amis` : "aucun filtre";
    }

    async function refresh() {
      const { data } = await getJSON(`/api/timeline?min_friend_likes=${minLikes}`);
      const posts = data.timeline || [];
      if (!posts.length) {
        feedEl.innerHTML = `<p class="muted">Aucun post à afficher.</p>`;
        return;
      }
      feedEl.innerHTML = posts
        .map(
          (p) => `
        <article class="post">
          <header>
            <strong>${esc(p.author_name || p.author_username || "?")}</strong>
            <span class="score" title="Score de proximité">score ${p.score}</span>
          </header>
          <p>${esc(p.content)}</p>
          <footer>
            <button data-like="${p.post_id}" class="${p.liked_by_me ? "liked" : ""}">
              ${p.liked_by_me ? "♥ Aimé" : "♡ J'aime"}
            </button>
            <span class="muted">${p.like_count} like(s)</span>
          </footer>
        </article>`
        )
        .join("");
      feedEl.querySelectorAll("button[data-like]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = parseInt(btn.getAttribute("data-like"), 10);
          const liked = btn.classList.contains("liked");
          await postJSON(liked ? "/api/posts/unlike" : "/api/posts/like", {
            post_id: id,
          });
          refresh();
        });
      });
    }

    const form = document.getElementById("post-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const ta = document.getElementById("post-content");
      const content = ta.value.trim();
      if (!content) return;
      const { res } = await postJSON("/api/posts", { content });
      if (res.ok) {
        ta.value = "";
        refresh();
      }
    });

    refresh();
  }

  // --- Social Discovery -----------------------------------------------------

  async function bootDiscoveryPage() {
    const user = await requireUser();
    if (!user) return;
    bindLogout();

    const minMutual = getSetting("sg_min_mutual", 0);
    const badge = document.getElementById("mutual-badge");
    if (badge) {
      badge.textContent =
        minMutual > 0 ? `filtre actif : ≥ ${minMutual} ami(s) commun(s)` : "aucun filtre";
    }

    const friendsEl = document.getElementById("friends");
    const suggEl = document.getElementById("suggestions");

    async function refresh() {
      const { data: f } = await getJSON("/api/friends");
      friendsEl.textContent = (f.friends || []).join(", ") || "—";
      const { data: s } = await getJSON(
        `/api/recommendations?min_mutual=${minMutual}`
      );
      const recos = s.recommendations || [];
      if (!recos.length) {
        suggEl.innerHTML = `<p class="muted">Aucune suggestion pour l'instant.</p>`;
        return;
      }
      suggEl.innerHTML = recos
        .map(
          (r) => `
        <li class="sugg">
          <span><strong>${esc(r.username || r.user_id)}</strong>
            <span class="muted">${r.mutual_friends} ami(s) commun(s)</span></span>
          <button data-add="${r.user_id}">Ajouter</button>
        </li>`
        )
        .join("");
      suggEl.querySelectorAll("button[data-add]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = parseInt(btn.getAttribute("data-add"), 10);
          await postJSON("/api/friends/add", { friend_id: id });
          refresh();
        });
      });
    }

    const addForm = document.getElementById("add-friend-form");
    if (addForm) {
      addForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const input = document.getElementById("friend-id");
        const id = parseInt(input.value, 10);
        if (!Number.isInteger(id)) return;
        await postJSON("/api/friends/add", { friend_id: id });
        input.value = "";
        refresh();
      });
    }

    refresh();
  }

  // --- Gate Settings --------------------------------------------------------

  async function bootSettingsPage() {
    const user = await requireUser();
    if (!user) return;
    bindLogout();

    const likes = document.getElementById("min-friend-likes");
    const mutual = document.getElementById("min-mutual");
    const likesOut = document.getElementById("min-friend-likes-out");
    const mutualOut = document.getElementById("min-mutual-out");

    likes.value = getSetting("sg_min_friend_likes", 0);
    mutual.value = getSetting("sg_min_mutual", 0);
    likesOut.textContent = likes.value;
    mutualOut.textContent = mutual.value;

    likes.addEventListener("input", () => {
      likesOut.textContent = likes.value;
      setSetting("sg_min_friend_likes", likes.value);
    });
    mutual.addEventListener("input", () => {
      mutualOut.textContent = mutual.value;
      setSetting("sg_min_mutual", mutual.value);
    });
  }

  window.SocialGate = {
    bindRegisterForm,
    bindLoginForm,
    bootHomePage,
    bootTimelinePage,
    bootDiscoveryPage,
    bootSettingsPage,
  };
})();
