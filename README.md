# Algo_project — Social Gate / ASNAP

Projet semestriel **II.2415 — Advanced Algorithms and Programming**
(A2-S4 2025/2026, Pr Ammar Kheirbek).

**ASNAP** (Advanced Social Network Algorithms Platform) : le moteur
algorithmique du réseau social **Social Gate**, bâti autour d'un **modèle de
graphe** et entièrement aligné sur la base de connaissances du cours (lectures
+ labs). Rapport complet : [`REPORT.md`](REPORT.md).

> Tout le code n'utilise que la **bibliothèque standard de Python** — aucun
> framework, aucun SGBD, aucune dépendance externe (`pip install` inutile).
> Chaque algorithme est notre propre implémentation et cite sa source de cours.

---

## Fonctionnalités

| Service (slide 5) | Algorithme principal | Source cours |
|---|---|---|
| **Login** | BST + hash maps | L10 / LAB8, LAB1 |
| **Social Discovery** (reco amis) | BFS amis-d'amis (distance 2) + amis communs | L8 / LAB6 Ex.3 + LAB2 Ex.2 |
| **Gate Timeline** (feed trié) | score de proximité + **MergeSort** | sujet s6 + LAB4 Ex.2 / L9 |
| **Gate Settings** (filtres) | seuils de confiance | sujet s5 |
| **Intelligence ASNAP** | communautés (composantes connexes), influenceurs (dominating set), coloring, knapsack, independent set, min cut | L8 + LAB9 + LAB10 |

---

## Lancer le serveur

Python ≥ 3.10, depuis la racine du repo :

```bash
python -m backend.server --host 127.0.0.1 --port 8000
```

Ouvrir <http://127.0.0.1:8000/>. Pages : `/register.html`, `/login.html`,
`/home.html` (hub), `/timeline.html`, `/discovery.html`, `/settings.html`.

Données persistées dans `data/*.json` (créés au premier usage) :
`users.json`, `friends.json`, `posts.json`. Supprimer ces fichiers réinitialise.

**Données de démo** (pour une présentation déjà peuplée) :

```bash
python -m backend.seed_demo --reset   # 8 users, 2 communautés, posts + likes
```

Connexion ensuite avec n'importe quel prénom (`alice`, `bob`, …) et le mot de
passe `password1`. Penser à redémarrer le serveur après le seed.

Options CLI : `--host`, `--port`, `--db` (users.json).

---

## Tests & benchmarks

```bash
python -m unittest discover -s tests -v   # 118 tests, tous verts
python benchmark.py                        # exact vs glouton (voir BENCHMARKS.md)
```

---

## Endpoints API (JSON)

| Méthode | URL | Description |
|---|---|---|
| POST | `/api/register` `/api/login` `/api/logout` | authentification |
| GET | `/api/me` | profil courant |
| POST | `/api/friends/add` `/api/friends/remove` | gérer les amitiés |
| GET | `/api/friends` | liste d'amis |
| GET | `/api/recommendations?min_mutual=N` | suggestions d'amis |
| POST | `/api/posts` `/api/posts/like` `/api/posts/unlike` | posts & likes |
| GET | `/api/timeline?min_friend_likes=N` | feed trié par score |
| GET | `/api/communities` | composantes connexes |
| GET | `/api/influencers` | dominating set glouton |

Cookie `session` `HttpOnly; SameSite=Strict`.

---

## Architecture du dossier

```
backend/
  bst.py            BST (L10 / LAB8)
  auth.py           hash mot de passe + SessionStore
  user_store.py     BST + hash maps + persistance JSON
  graph.py          SocialGraph : liste+matrice d'adjacence, BFS, DFS, composantes (L8/LAB6)
  social_store.py   bridge users <-> graphe + persistance amitiés
  recommendation.py amis communs + amis-d'amis (LAB2 Ex2 / LAB6 Ex3)
  feed.py           score de proximité + MergeSort (sujet s6 / LAB4 / L9)
  filters.py        seuils de confiance (sujet s5)
  hard_problems.py  LAB9/LAB10 : dominating set, coloring, knapsack, independent set, min cut
  datasets.py       générateurs de graphes (tailles variées)
  server.py         http.server : toutes les routes JSON + service statique
frontend/           index/login/register/home/timeline/discovery/settings + app.js + styles.css
pseudocode/         pseudo-code (règles Lecture 2) : AUTH, GRAPH, RECO, FEED, SETTINGS, HARDPROBLEMS
tests/              8 fichiers de tests unittest
benchmark.py        mesures de performance      BENCHMARKS.md  résultats
REPORT.md           rapport final
```

---

## Alignement cours & authenticité

Chaque module a été audité contre les **vrais PDF du cours**. Les éléments qui
relèvent du **sujet** (score de proximité ami=10/inconnu=1, seuils de confiance)
ou de **choix d'implémentation** (persistance JSON, stabilité du MergeSort) sont
explicitement étiquetés comme tels et jamais présentés comme « issus du cours ».
Détails dans [`REPORT.md`](REPORT.md) §6.

---

## Divergence assumée : MySQL

Le sujet (slide 7) mentionne MySQL, mais le cours ne couvre aucun SGBD. La
persistance utilise donc le type **`File`** (Lecture 3, slide 30) — fichiers
JSON. La logique de stockage est isolée dans les `*Store`, rendant un futur
passage à MySQL trivial.
