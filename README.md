# Algo_project — Social Gate

Projet semestriel **II.2415 — Advanced Algorithms and Programming**
(A2-S4 2025/2026, Pr Ammar Kheirbek).

Cette première itération implémente la couche **Login** de l'architecture
Social Gate (slide 4 du sujet) : *Interface* + *Backend Interface* + une
*Database* simple en mémoire.

---

## Stack

Tout est strictement aligné sur les supports du cours et n'utilise que la
**bibliothèque standard de Python**.

| Couche                       | Choix                                  | Source cours                          |
|------------------------------|----------------------------------------|----------------------------------------|
| Serveur HTTP                 | `http.server` (stdlib)                 | minimal, sans framework                |
| Index `user_id → User`       | **BST**                                | Lecture 10 / **LAB 8 Ex.1**            |
| Index `username → user_id`   | **Hash map** (`dict`)                  | LAB 1 Ex.6 / question finale LAB 8     |
| Index `email → user_id`      | Hash map                               | idem                                   |
| Sessions `token → user_id`   | Hash map                               | idem                                   |
| Hash mot de passe            | `hashlib.sha256(salt ‖ password)`      | stdlib                                 |
| Persistance                  | Fichier JSON (type `File`, Lecture 3)  | aucun SGBD utilisé                     |
| Frontend                     | HTML + CSS + JavaScript vanilla        | sans framework                         |

Aucune dépendance externe : `pip install` n'est pas nécessaire.

---

## Lancer le serveur

Depuis la racine du repo, avec Python ≥ 3.10 :

```bash
python -m backend.server --host 127.0.0.1 --port 8000
```

Puis ouvrir <http://127.0.0.1:8000/> dans un navigateur.

* `/login.html` — connexion par nom d'utilisateur **ou** email.
* `/register.html` — inscription (username, email, prénom, nom, date de
  naissance, mot de passe ≥ 8 caractères).
* `/home.html` — page protégée affichant le profil courant.

Les utilisateurs sont persistés dans `data/users.json` (créé
automatiquement au premier `register`). Pour réinitialiser la base,
supprimer ce fichier.

### Options CLI

```
--host    adresse d'écoute (défaut 0.0.0.0)
--port    port d'écoute    (défaut 8000)
--db      chemin du fichier JSON (défaut data/users.json)
```

---

## Lancer les tests

```bash
python -m unittest discover -s tests -v
```

Couvre :

* `test_bst.py` — opérations BST (insert / search / delete des trois cas /
  in-order trié / arbre dégénéré).
* `test_auth.py` — hash + sel aléatoire + comparaison constante + unicité
  des tokens de session sur 2 000 tirages.
* `test_user_store.py` — validation des champs, duplicates, authentification
  par username **ou** email, round-trip JSON.

---

## Architecture du dossier

```
backend/
  bst.py         BST (LAB 8 Ex.1) — clé entière, valeur opaque
  auth.py        hash mot de passe + SessionStore (hash map)
  user_store.py  BST + 2 hash maps + persistance JSON
  server.py      http.server : /api/register, /api/login, /api/logout, /api/me
frontend/
  index.html     redirection /login si pas connecté, /home sinon
  login.html     formulaire de connexion
  register.html  formulaire d'inscription
  home.html      page protégée + bouton de déconnexion
  styles.css     style minimaliste (sombre)
  app.js         glue fetch() pour les 3 pages
pseudocode/
  AUTH_pseudocode.md   pseudo-code commenté selon les règles de la Lecture 1
tests/
  test_bst.py
  test_auth.py
  test_user_store.py
```

---

## Endpoints

| Méthode | URL              | Corps JSON                                                                                  | Réponse                          |
|---------|------------------|---------------------------------------------------------------------------------------------|----------------------------------|
| POST    | `/api/register`  | `{username, email, first_name, last_name, birth_date, password}`                            | `201 {user}` + cookie `session`  |
| POST    | `/api/login`     | `{username | email, password}`                                                              | `200 {user}` + cookie `session`  |
| POST    | `/api/logout`    | —                                                                                           | `200 {ok: true}`                 |
| GET     | `/api/me`        | —                                                                                           | `200 {user}` ou `401`            |

Le cookie `session` est `HttpOnly; SameSite=Strict` ; côté frontend, toutes
les requêtes utilisent `credentials: "same-origin"`.

---

## Complexité (résumé)

Pour `n` utilisateurs en base :

| Opération          | Moyenne      | Pire cas |
|--------------------|--------------|----------|
| Inscription        | O(log n)     | O(n)     |
| Connexion          | O(log n)     | O(n)     |
| Déconnexion        | O(1)         | O(1)     |
| `/api/me`          | O(log n)     | O(n)     |
| Sauvegarde / chargement JSON | O(n) | O(n)     |

Détails et justification dans
[`pseudocode/AUTH_pseudocode.md`](pseudocode/AUTH_pseudocode.md).

---

## Limites volontaires

* Pas de réinitialisation de mot de passe ni de vérification d'email
  (hors-cours).
* Pas de MySQL : la persistance JSON est un placeholder pédagogique. Le
  passage à MySQL est prévu pour une itération ultérieure (cf. slide 7
  du sujet) — l'interface `UserStore` est volontairement compatible avec
  un backend SQL.
* La BST n'est pas auto-rééquilibrante. Une montée à un AVL (Lecture 10
  slides 21–26) est triviale puisque la signature de `BST` est isolée.
