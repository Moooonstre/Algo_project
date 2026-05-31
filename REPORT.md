# ASNAP / Social Gate — Rapport final

Projet semestriel II.2415 — *Advanced Algorithms and Programming* (A2-S4 2025/2026).
Réseau social **Social Gate**, moteur **ASNAP** (Advanced Social Network
Algorithms Platform).

> **Principe directeur** : tout le contenu algorithmique provient **uniquement**
> de la base de connaissances du cours (lectures + labs). Chaque module cite sa
> source. Les écarts (persistance, score de proximité) sont des éléments du
> **sujet** ou des choix d'implémentation, explicitement signalés comme tels.

---

## 1. Architecture (slide 4 du sujet)

```
User → Interface (frontend HTML/CSS/JS)
        → Backend Interface (http.server, endpoints JSON)
        → DataBase (persistance fichier JSON, type File — Lecture 3)
        → Classification (algorithmes : graphe, tri, recommandation, NP-hard)
```

Pile **100 % bibliothèque standard Python** (aucun framework : ni Flask, ni
ORM, ni React — rien de cela n'est au programme) :

| Couche | Choix | Source cours |
|---|---|---|
| Serveur HTTP | `http.server` (stdlib) | minimal, hors-framework |
| Index utilisateurs | **BST** clé `user_id` | Lecture 10 + LAB 8 Ex.1 |
| Index username/email/session | **Hash maps** | LAB 1 / LAB 8 |
| Graphe social | **liste + matrice d'adjacence** | Lecture 8 + LAB 6 |
| Hash mot de passe | `hashlib.sha256(sel‖mdp)` | stdlib |
| Persistance | fichiers **JSON** (type `File`) | Lecture 3 slide 30 |
| Frontend | HTML + CSS + JS vanilla | hors-framework |

---

## 2. Modules et algorithmes (tous notre implémentation)

| Module | Fonction | Algorithme | Source | Complexité |
|---|---|---|---|---|
| `bst.py` | recherche/insertion/suppression utilisateur | BST | L10 / LAB8 | O(log n) moy. |
| `graph.py` | `bfs_levels`, `nodes_at_distance` | **BFS** (file FIFO) | L8 / LAB6 | O(N+E) |
| `graph.py` | `dfs_preorder` | **DFS** (pile) | L8 s27 / LAB6 | O(N+E) |
| `graph.py` | `shortest_path` | plus court chemin (BFS) | L8 / LAB6 | O(N+E) |
| `graph.py` | `connected_components` | composantes connexes = communautés | L8 | O(N+E) |
| `recommendation.py` | `mutual_friends` | intersection d'ensembles | LAB2 Ex.2 | O(min deg) |
| `recommendation.py` | `recommend_friends` | amis-d'amis (BFS d=2) classés par amis communs | LAB6 Ex.3 + LAB2 Ex.2 | O(N+E) |
| `feed.py` | `proximity_score` | like ami=10 / inconnu=1 | sujet slide 6 | O(L) |
| `feed.py` | `merge_sort` / `rank_timeline` | **MergeSort** (diviser-pour-régner) | LAB4 Ex.2 / L9 | O(n log n) |
| `filters.py` | seuils de confiance | filtre (sujet) sur primitives cours | sujet slide 5 | O(P·L̄) |
| `hard_problems.py` | dominating set | brute force + glouton | LAB9 Ex.1 | O(2^N) / O(N(N+E)) |
| `hard_problems.py` | graph coloring | backtracking | LAB9 Ex.2 | O(k^N) |
| `hard_problems.py` | knapsack 0/1 | **DP** + glouton | LAB9 Ex.3 / LAB10 Ex.2 | O(N·budget) |
| `hard_problems.py` | max independent set | backtracking + élagage | LAB10 Ex.1 | O(2^N) élagué |
| `hard_problems.py` | balanced min cut | recherche locale | LAB10 Ex.3 | O(iter·N·E) |

Pseudo-code détaillé (règles **Lecture 2, slides 10-18**) dans `pseudocode/`.

---

## 3. Services du site (slide 5)

* **Gate Timeline** — feed trié par score de proximité (MergeSort).
* **Social Discovery** — suggestions d'amis (amis-d'amis + amis communs).
* **Gate Settings** — seuils de confiance (likes d'amis, amis communs).
* **Home hub** — navigation + aperçu de l'intelligence (communautés,
  ensemble d'influenceurs).

API JSON : `/api/register|login|logout|me`, `/api/friends[/add|/remove]`,
`/api/recommendations`, `/api/posts[/like|/unlike]`, `/api/timeline`,
`/api/communities`, `/api/influencers`.

---

## 4. Tests, datasets & performance (section 3 du sujet)

* **118 tests unitaires** (`python -m unittest discover -s tests`), tous verts.
* Cas limites des labs couverts : graphe vide, complet, sans arête, N=1,
  budget=0, exact vs glouton.
* Générateurs de datasets de tailles variées (`datasets.py` : empty/path/star/
  complete/random Erdős–Rényi).
* Benchmarks `benchmark.py` → `BENCHMARKS.md` : l'exact explose avec N (NP-Hard),
  le glouton/DP restent rapides — illustre « vérification facile vs construction
  difficile » (Lecture 11).

---

## 5. Un défi technique et sa résolution

**Problème** : le sujet (slide 7) impose MySQL, mais le cours ne couvre **aucun
SGBD**. Suivre MySQL aurait introduit des concepts hors-programme.

**Solution** : rester strictement aligné cours en utilisant le type **`File`**
(Lecture 3, slide 30) — persistance par fichiers JSON, avec écriture atomique
(`tmp` + `os.replace`). Toute la logique de stockage est isolée dans les
`*Store`, ce qui rendrait un passage ultérieur à MySQL trivial. Divergence
**assumée et documentée**.

---

## 6. Vérification d'authenticité (alignement cours)

Chaque bloc a été audité par relecture des **vrais PDF du cours** (équipe
d'agents). Corrections apportées suite aux audits :
* références de lecture rectifiées (pseudo-code = Lecture 2 ; DFS itératif =
  Lecture 8 s27 ; pas de fausse « Lecture 6 ») ;
* stabilité du MergeSort présentée comme **propriété démontrée par nous**
  (le cours ne traite pas la stabilité) ;
* classification P/NP-Hard rattachée honnêtement à la Lecture 11 (Dominating
  Set / Independent Set / Min Cut non cités tels quels → rattachés à
  Vertex Cover / Clique. *Hors cours* (théorie de la complexité générale, non
  énoncée dans la Lecture 11) : le min-cut **non contraint** est polynomial —
  dual du max-flow, lui cité en P dans la Lecture 11 — et c'est la contrainte
  d'**équilibre 40 %** qui rend notre version NP-Hard) ;
* éléments hors-cours (score de proximité, seuils, persistance JSON) étiquetés
  **sujet ASNAP** ou **choix d'implémentation**, jamais présentés comme « cours ».

---

## 7. Limites et suite possible

* BST non auto-équilibrante (montée en AVL triviale, signature isolée).
* Exact infaisable au-delà de ~N=20 (attendu pour des problèmes NP-Hard) ;
  les heuristiques gloutonnes prennent le relais à l'échelle.
* Frontend volontairement minimal (pas de framework, conforme au cours).
