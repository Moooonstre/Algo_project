# Pseudo-code — Cœur graphe (ASNAP / Social Gate)

> Toutes les structures et tous les algorithmes proviennent du cours
> *Advanced Algorithms and Programming* (II.2415) :
> **Lecture 8 — Graph Data Structures** et **LAB 6 — Basics of Graphs**.
> Conventions de pseudo-code : règles de programmation structurée vues en
> **Lecture 2 (Introduction to Advanced Algorithms), slides 10-18**
> (« Some rules for structural programming » : lisibilité, modularité, pas de
> Goto, description avant code, contrôle de la récursion).
> Le sujet ASNAP impose que *tous les algorithmes de graphe soient notre
> propre implémentation* et que *le système soit bâti autour d'un modèle de
> graphe* : c'est le rôle de ce module.

---

## 1. Structures de données

### 1.1 Graphe social (non orienté, non pondéré)

> Référence : LAB 6 Ex.1 (liste vs matrice d'adjacence), Lecture 8.

```
Type Graphe = Record {
    adj : HashMap<Entier, Ensemble<Entier>>   // user_id → ensemble d'amis
}
```

* Sommets = `user_id` (entiers), un par utilisateur inscrit.
* Arêtes  = amitiés **non orientées** : si `a` est ami de `b`, alors `b` est
  ami de `a`.

> **Adaptation assumée** : la Lecture 8 décrit la liste d'adjacence comme
> `array[1..n] of Pvertex` (une *liste chaînée triée* de voisins par sommet).
> Nous l'adaptons en `HashMap<Entier, Ensemble>` en réutilisant la structure
> **Ensemble (Set)** de LAB 2, pour un accès/insertion en O(1) moyen ; la sortie
> ordonnée (ex. liste d'amis) est obtenue par tri explicite.

### 1.2 Vue matrice d'adjacence (à la demande)

```
Fonction VersMatrice(G : Graphe) → (ids : Liste<Entier>, M : Matrice)
    ids ← Trier(Clés(G.adj))
    index ← HashMap vide
    pour i de 0 à |ids|-1 faire  index[ids[i]] ← i  fin pour
    M ← matrice |ids|×|ids| remplie de 0
    pour chaque (a, amis) dans G.adj faire
        pour chaque b dans amis faire
            si b ∈ index alors  M[index[a]][index[b]] ← 1  fin si
        fin pour
    fin pour
    retourner (ids, M)
fin // VersMatrice — O(N²)
```

---

## 2. Opérations de base

```
Procédure AjouterUtilisateur(G, u)
    si u ∉ G.adj alors  G.adj[u] ← Ensemble vide  fin si      // O(1) moy.
fin

Procédure AjouterAmitié(G, a, b)
    si a = b alors lever Erreur("auto-amitié interdite") fin si
    si a ∉ G.adj ou b ∉ G.adj alors lever Erreur("utilisateur inconnu") fin si
    G.adj[a] ← G.adj[a] ∪ {b}                                  // O(1) moy.
    G.adj[b] ← G.adj[b] ∪ {a}
fin

Fonction SontAmis(G, a, b) → Booléen
    retourner a ∈ G.adj et b ∈ G.adj[a]                        // O(1) moy.
fin
```

---

## 3. Parcours en largeur — BFS (Lecture 8, LAB 6 Ex.2/Ex.3)

```
Fonction BFS_Niveaux(G, source) → HashMap<Entier, Entier>
    // retourne {sommet_atteint : distance_en_sauts depuis source}
    si source ∉ G.adj alors lever Erreur("source inconnue") fin si
    distance ← HashMap vide
    distance[source] ← 0
    file ← File vide
    Enfiler(file, source)
    tant que file non vide faire
        courant ← Défiler(file)
        pour chaque ami dans G.adj[courant] faire
            si ami ∉ distance alors
                distance[ami] ← distance[courant] + 1
                Enfiler(file, ami)
            fin si
        fin pour
    fin tant que
    retourner distance
fin // BFS_Niveaux — O(N + E) : chaque sommet et chaque arête vus une fois
```

Dérivés directs (base du service *Social Discovery* du sujet ASNAP — ces
fonctions viennent de **LAB 6 Ex.3**, pas d'une slide du cours) :

```
Fonction SommetsADistance(G, source, k) → Ensemble
    retourner { u | (u, d) ∈ BFS_Niveaux(G, source) et d = k }
fin

Fonction AmisDansKSauts(G, source, k) → Ensemble        // LAB 6 Ex.3
    retourner { u | (u, d) ∈ BFS_Niveaux(G, source) et 1 ≤ d ≤ k }
fin
```

* `SommetsADistance(G, source, 1)` = amis directs.
* `SommetsADistance(G, source, 2)` = **amis d'amis** (distance 2).

---

## 4. Plus court chemin non pondéré (Lecture 8)

```
Fonction PlusCourtChemin(G, source, cible) → Liste<Entier> ∪ ⟂
    si source = cible alors retourner [source] fin si
    parent ← HashMap vide ; parent[source] ← source
    file ← File vide ; Enfiler(file, source)
    tant que file non vide faire
        courant ← Défiler(file)
        pour chaque ami dans G.adj[courant] faire
            si ami ∉ parent alors
                parent[ami] ← courant
                si ami = cible alors
                    retourner ReconstruireChemin(parent, source, cible)
                fin si
                Enfiler(file, ami)
            fin si
        fin pour
    fin tant que
    retourner ⟂                                   // cible inatteignable
fin // O(N + E)
```

---

## 5. Parcours en profondeur — DFS (Lecture 8 slide 27 / LAB 6 Ex.2 Part B)

> La version itérative à pile explicite est donnée **directement en Lecture 8
> (slide 27)** et en **LAB 6 Ex.2 Part B** — ce n'est pas une « conversion »
> ajoutée de notre part.

```
Fonction DFS_Préordre(G, source) → Liste<Entier>
    visités ← Ensemble vide ; ordre ← Liste vide
    pile ← Pile vide ; Empiler(pile, source)
    tant que pile non vide faire
        courant ← Dépiler(pile)
        si courant ∈ visités alors continuer fin si
        visités ← visités ∪ {courant}
        Ajouter(ordre, courant)
        pour chaque ami dans Trier(G.adj[courant], décroissant) faire
            si ami ∉ visités alors Empiler(pile, ami) fin si
        fin pour
    fin tant que
    retourner ordre
fin // O(N + E)
```

---

## 6. Composantes connexes (Lecture 8)

```
Fonction ComposantesConnexes(G) → Liste<Liste<Entier>>
    vus ← Ensemble vide ; composantes ← Liste vide
    pour chaque départ dans G.adj faire
        si départ ∈ vus alors continuer fin si
        comp ← Trier(Clés(BFS_Niveaux(G, départ)))
        vus ← vus ∪ comp
        Ajouter(composantes, comp)
    fin pour
    retourner composantes
fin // O(N + E) : chaque sommet/arête visité une seule fois au total
```

Une composante connexe = un sous-graphe connexe maximal (Lecture 8 slide 11),
trouvée en lançant un parcours (DFS slide 28, ou BFS slides 32/36) depuis chaque
sommet non visité. C'est la notion du cours la plus proche de la « communauté »
du sujet ASNAP (« communauté » étant un terme du sujet, pas du cours).

---

## 7. Récapitulatif de complexité

| Opération                         | Complexité      | Source           |
|-----------------------------------|-----------------|------------------|
| AjouterUtilisateur / SontAmis     | O(1) moyen      | LAB 6 Ex.1       |
| AjouterAmitié / RetirerAmitié     | O(1) moyen      | LAB 6 Ex.1       |
| Voisins / Degré                   | O(1) / O(degré) | LAB 6 Ex.1       |
| BFS_Niveaux / PlusCourtChemin     | O(N + E)        | Lecture 8, LAB 6 |
| AmisDansKSauts / SommetsADistance | O(N + E)        | LAB 6 Ex.3       |
| DFS_Préordre                      | O(N + E)        | Lecture 8        |
| ComposantesConnexes               | O(N + E)        | Lecture 8        |
| VersMatrice                       | O(N²)           | LAB 6 Ex.1       |

> **Liste vs matrice d'adjacence** (LAB 6) : la liste coûte O(N + E) en mémoire
> et rend les parcours linéaires ; la matrice coûte O(N²) mais répond à
> « a et b sont-ils amis ? » en O(1). Pour un réseau social réel (graphe
> **creux**), la liste d'adjacence est le bon choix — d'où le choix primaire ici.

---

## 8. Cas limites couverts par les tests (`tests/test_graph.py`)

* Graphe vide (0 sommet), arêtes vides (sommets isolés).
* Auto-amitié rejetée, amitié vers un utilisateur inconnu rejetée.
* Ajout d'amitié en double (idempotent), suppression d'amitié/sommet.
* BFS : niveaux, amis-d'amis (distance 2), k-sauts, cible inatteignable (⟂).
* DFS : ordre déterministe.
* Composantes connexes : plusieurs communautés + nœud isolé.
* Matrice d'adjacence : triangle, graphe vide (tout à 0), graphe complet
  (tout à 1 hors diagonale).
* Round-trip de persistance (`tests/test_social_store.py`), nœud isolé conservé.
