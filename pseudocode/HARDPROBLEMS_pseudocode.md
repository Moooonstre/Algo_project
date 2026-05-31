# Pseudo-code — Algorithmes avancés (LAB 9 & LAB 10)

> Sources, aucune procédure inventée : **LAB 9** (Influencer Coverage =
> dominating set ; Conflict-Free Labeling = graph coloring ; Ad Campaign =
> knapsack) et **LAB 10** (Event Invitation = max independent set ; Viral
> Message = knapsack ; Group Formation = balanced min cut). Concepts de
> complexité (P / NP / NP-Complete / NP-Hard, vérification vs construction) :
> **Lecture 11 (Advanced Algorithm Complexity)**.
> Détection de communautés = composantes connexes (Lecture 8) — voir
> `GRAPH_pseudocode.md`. Conventions de pseudo-code : **Lecture 2, slides 10-18**.

---

## 1. Influencer Coverage — minimum dominating set (LAB 9 Ex.1)

```
Fonction EstCouvertureValide(sel, G) → Booléen          // O(N + E)
    couverts ← Ensemble(sel)
    pour chaque u dans sel faire couverts ← couverts ∪ Voisins(G, u) fin pour
    retourner (∀ u ∈ G : u ∈ couverts)
fin

Fonction CouvertureMinimale(G) → (taille, liste)        // exact, O(2^N·(N+E))
    pour taille de 0 à N faire
        pour chaque sous-ensemble S de taille `taille` faire
            si EstCouvertureValide(S, G) alors retourner (taille, S) fin si
        fin pour
    fin pour
fin  // force brute, faisable N ≤ 20 (LAB 9)

Fonction CouvertureRapide(G) → (taille, liste)          // glouton, O(N·(N+E))
    nonCouverts ← tous les sommets ; sel ← ∅
    tant que nonCouverts ≠ ∅ faire
        choisir u maximisant |({u} ∪ Voisins(u)) ∩ nonCouverts|
        sel ← sel ∪ {u} ; nonCouverts ← nonCouverts \ ({u} ∪ Voisins(u))
    fin tant que
    retourner (|sel|, sel)
fin
```

---

## 2. Conflict-Free Labeling — graph coloring (LAB 9 Ex.2)

```
Fonction EtiquetageValide(lab, G) → Booléen             // O(E)
    pour chaque arête (u,v) ∈ G faire
        si lab[u] = lab[v] alors retourner Faux fin si
    fin pour
    retourner Vrai
fin

Fonction AssignerCouleurs(k, G) → (succès, lab)         // backtracking, O(k^N)
    sommets ← Trier(Sommets(G))
    Fonction Retour(i)
        si i = |sommets| alors retourner Vrai fin si
        u ← sommets[i]
        utilisées ← { lab[w] | w ∈ Voisins(u), w étiqueté }
        pour couleur de 0 à k-1 faire
            si couleur ∉ utilisées alors
                lab[u] ← couleur
                si Retour(i+1) alors retourner Vrai fin si
                effacer lab[u]
            fin si
        fin pour
        retourner Faux
    fin
    retourner (Retour(0), lab)
fin

Fonction MinCouleurs(G) → (k, lab)                       // nombre chromatique
    pour k de 1 à N faire
        (ok, lab) ← AssignerCouleurs(k, G)
        si ok alors retourner (k, lab) fin si
    fin pour
fin   // graphe sans arête → k=1 ; complet K_n → k=n
```

---

## 3. Ad Campaign / Viral Message — 0/1 knapsack (LAB 9 Ex.3 / LAB 10 Ex.2)

```
Fonction DansLeBudget(sel, coûts, budget) → Booléen      // O(N)
    retourner Somme(coûts[i] pour i ∈ sel) ≤ budget
fin

Fonction MaximiserPortée(budget, coûts, infl) → (max, sel)   // DP, O(N·budget)
    dp ← table (N+1)×(budget+1) initialisée à 0
    pour i de 1 à N faire
        pour w de 0 à budget faire
            dp[i][w] ← dp[i-1][w]                         // ne pas prendre i
            si coûts[i-1] ≤ w alors
                dp[i][w] ← max(dp[i][w],
                               dp[i-1][w-coûts[i-1]] + infl[i-1])   // prendre i
            fin si
        fin pour
    fin pour
    // reconstruction du sous-ensemble choisi
    w ← budget ; sel ← ∅
    pour i de N à 1 faire
        si dp[i][w] ≠ dp[i-1][w] alors sel ← sel ∪ {i-1} ; w ← w - coûts[i-1] fin si
    fin pour
    retourner (dp[N][budget], sel)
fin

Fonction StratégieRapide(budget, coûts, infl) → (portée, sel)   // glouton ratio
    trier les items par infl[i]/coûts[i] décroissant
    prendre chaque item tant qu'il rentre dans le budget
fin
```

> DP = pseudo-polynomial O(N·budget), **pas** exponentiel en N car la table est
> indexée par le budget — d'où l'impossibilité avec des coûts réels (LAB 9/10).

---

## 4. Event Invitation — maximum independent set (LAB 10 Ex.1)

```
Fonction InvitationValide(inv, G) → Booléen              // O(k²)
    pour chaque paire (a,b) ⊆ inv faire
        si SontAmis(G, a, b) alors retourner Faux fin si
    fin pour
    retourner Vrai
fin

Fonction MaxInvitationsExact(G) → (taille, liste)        // backtracking + élagage
    sommets ← Trier(Sommets(G)) ; meilleur ← ∅
    Fonction Retour(i, courant)
        si |courant| + (N - i) ≤ |meilleur| alors retourner fin si   // ÉLAGAGE
        si i = N alors
            si |courant| > |meilleur| alors meilleur ← courant fin si ; retourner
        fin si
        u ← sommets[i]
        si (∀ c ∈ courant : ¬SontAmis(u, c)) alors      // inclure u
            Retour(i+1, courant ∪ {u})
        fin si
        Retour(i+1, courant)                            // exclure u
    fin
    Retour(0, ∅) ; retourner (|meilleur|, meilleur)
fin

Fonction MaxInvitationsGlouton(G) → (taille, liste)      // O(N²)
    restants ← Sommets(G) ; inv ← ∅
    tant que restants ≠ ∅ faire
        u ← sommet de restants de plus petit degré (dans restants)
        inv ← inv ∪ {u} ; restants ← restants \ ({u} ∪ Voisins(u))
    fin tant que
    retourner (|inv|, inv)
fin
```

---

## 5. Group Formation — balanced minimum cut (LAB 10 Ex.3)

```
Fonction AretesCoupees(A, B, G) → Entier                 // O(E)
    retourner |{ (u,v) ∈ G : (u∈A ∧ v∈B) ∨ (u∈B ∧ v∈A) }|
fin

Fonction PartitionGloutonne(G, initiale) → (coupe, A, B)
    tailleMin ← ⌈0.4 · N⌉                                // chaque groupe ≥ 40%
    (A, B) ← initiale ou split équilibré par défaut
    répéter
        amélioré ← Faux
        pour chaque sommet u faire
            si déplacer u (en respectant l'équilibre) réduit les arêtes coupées
            alors déplacer u ; amélioré ← Vrai fin si
        fin pour
    jusqu'à ¬amélioré
    retourner (AretesCoupees(A,B,G), A, B)
fin

Fonction PartitionRechercheLocale(G, itérations) → (coupe, A, B)
    meilleur ← ⟂
    répéter `itérations` fois
        split aléatoire respectant l'équilibre 40%
        (coupe, A, B) ← PartitionGloutonne(G, split)
        si coupe < meilleur.coupe alors meilleur ← (coupe, A, B) fin si
    fin répéter
    retourner meilleur
fin
```

---

## 6. Classification (questions d'intégration LAB 9 / LAB 10, Lecture 11)

| Problème (exercice)                         | Vérification | Optimisation     | Appui cours |
|---------------------------------------------|--------------|------------------|-------------|
| Dominating set (LAB 9 Ex.1)                 | P (O(N+E))   | **NP-Hard**      | non cité en L11 ; rattaché au **Vertex Cover** (NP-Complete, L11 slides 14/18 — LAB 9 « Vertex Cover variant ») |
| Graph coloring (LAB 9 Ex.2)                 | P (O(E))     | **NP-Hard** (k≥3 décision NP-Complete) | **L11 slides 10/14/18** (réduction depuis 3-SAT) |
| 0/1 Knapsack (LAB 9 Ex.3 / LAB 10 Ex.2)     | P (O(N))     | **NP-Hard** (décision NP-Complete ; DP pseudo-poly) | **L11 slide 18** (réduction depuis Subset Sum) |
| Max independent set (LAB 10 Ex.1)           | P (O(k²))    | **NP-Hard**      | non cité en L11 ; équivalent à **Clique** / complément du **Vertex Cover** (L11 slides 14/18) |
| Balanced min cut (LAB 10 Ex.3)              | P (O(E))     | **NP-Hard** *(à cause de la contrainte d'équilibre)* | non cité en L11 ; le min-cut **non contraint** est P (dual du max-flow, L11 slide 12) — c'est l'équilibre 40 % qui rend NP-Hard |
| Composantes connexes (communautés)          | —            | **P** (O(N+E))   | classe P (L11) ; parcours de graphe (L8) |

> **Vérification facile vs construction difficile** : pour tous ces problèmes,
> vérifier une solution candidate est polynomial (colonne « Vérification »),
> alors que trouver l'optimum est NP-Hard ⇒ on utilise l'exact seulement pour
> les petites instances, et des approximations gloutonnes / recherche locale à
> grande échelle (réponses aux questions des LAB 9 / LAB 10).

---

## 7. Récapitulatif de complexité

| Fonction                          | Complexité            |
|-----------------------------------|-----------------------|
| is_valid_coverage / labeling / invitation | O(N+E) / O(E) / O(k²) |
| find_minimum_coverage             | O(2^N·(N+E))          |
| find_fast_coverage                | O(N·(N+E))            |
| assign_labels / find_min_labels   | O(k^N) / Σ            |
| maximize_reach (DP)               | O(N·budget)           |
| fast_alternative_strategy         | O(N log N)            |
| find_max_invitations_exact        | O(2^N) avec élagage   |
| find_max_invitations_greedy       | O(N²)                 |
| count_cross_edges                 | O(E)                  |
| partition gloutonne / locale      | O(N·E) / O(iter·N·E)  |

---

## 8. Cas limites couverts (`tests/test_hard_problems.py`)

* Graphe vide, graphe complet K_n, graphe sans arête, budget = 0.
* Exact vs glouton : contre-exemple knapsack où le glouton est sous-optimal.
* Coloration : triangle ⇒ 3, K4 ⇒ 4, sans arête ⇒ 1, vide ⇒ 0.
* Independent set / dominating set : étoile, chemin, triangle.
* Coupe équilibrée : contrainte 40 %, recherche locale trouve la coupe minimale.
