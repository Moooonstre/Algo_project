/* Social Gate - frontend glue.
 *
 * Minimal vanilla JavaScript that wires the three HTML pages to the JSON
 * endpoints exposed by backend/server.py. We deliberately avoid any
 * dependency on a frontend framework (none is covered by the course).
 */
(function () {
  "use strict";

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

  function showError(el, message) {
    if (!el) {
      return;
    }
    el.textContent = message;
    el.hidden = false;
  }

  function clearError(el) {
    if (!el) {
      return;
    }
    el.hidden = true;
    el.textContent = "";
  }

  function setSubmitting(button, isSubmitting, idleLabel) {
    if (!button) {
      return;
    }
    button.disabled = isSubmitting;
    button.textContent = isSubmitting ? "…" : idleLabel;
  }

  function bindRegisterForm() {
    const form = document.getElementById("register-form");
    const errorEl = document.getElementById("register-error");
    const submit = document.getElementById("register-submit");
    if (!form) {
      return;
    }
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
    if (!form) {
      return;
    }
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

  async function bootHomePage() {
    try {
      const res = await fetch("/api/me", { credentials: "same-origin" });
      if (!res.ok) {
        window.location.replace("/login.html");
        return;
      }
      const { user } = await res.json();
      document.getElementById("display-name").textContent =
        user.first_name || user.username;
      document.getElementById("p-username").textContent = user.username;
      document.getElementById("p-email").textContent = user.email;
      document.getElementById("p-fullname").textContent =
        `${user.first_name} ${user.last_name}`.trim();
      document.getElementById("p-birth").textContent = user.birth_date;
      document.getElementById("p-created").textContent = user.created_at;
    } catch (_) {
      window.location.replace("/login.html");
      return;
    }

    const logoutBtn = document.getElementById("logout-btn");
    logoutBtn.addEventListener("click", async () => {
      logoutBtn.disabled = true;
      try {
        await fetch("/api/logout", {
          method: "POST",
          credentials: "same-origin",
        });
      } finally {
        window.location.replace("/login.html");
      }
    });
  }

  window.SocialGate = {
    bindRegisterForm,
    bindLoginForm,
    bootHomePage,
  };
})();
