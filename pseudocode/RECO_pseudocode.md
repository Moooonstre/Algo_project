# Pseudo-code — Recommandation d'amis (Social Discovery, ASNAP)

> Sources cours (II.2415), aucune procédure inventée :
> **LAB 2 Ex.2** (« Mutual Friends Detection Using Sets » : intersection
> d'ensembles + similarité de Jaccard) et **LAB 6 Ex.3** (`recommend_friends` :
> amis-d'amis non déjà amis, via BFS — Lecture 8).
> Conventions de pseudo-code : règles de programmation structurée vues en
> **Lecture 2, slides 10-18**.
> Construit sur le cœur graphe (voir `GRAPH_pseudocode.md`).

---

## 1. Amis communs — intersection d'ensembles (LAB 2 Ex.2)

```
Fonction AmisCommuns(G, a, b) → Liste<Entier>
    // les listes d'adjacence sont des Ensembles (Set, LAB 2)
    communs ← G.adj[a] ∩ G.adj[b]              // Intersection(set_a, set_b)
    retourner Trier(communs)
fin // O(min(degré(a), degré(b)))
```

> LAB 2 Ex.2 : deux utilisateurs, on calcule l'intersection de leurs ensembles
> d'amis. Exemple du lab : A={101..105}, B={103,104,106,107,108} ⇒ communs
> {103,104}.

---

## 2. Similarité de Jaccard (LAB 2 Ex.2, exigence 3)

```
Fonction Jaccard(G, a, b) → Réel
    fa ← G.adj[a] ; fb ← G.adj[b]
    union ← fa ∪ fb
    si union = ∅ alors retourner 0 fin si        // convention : aucun ami
    retourner |fa ∩ fb| / |union|
fin // « mutual friend coefficient » ∈ [0,1]
```

> LAB 2 Ex.2 : coefficient d'amis mutuels = |Intersection| / |Union| = la
> similarité de Jaccard des cercles sociaux. Exemple du lab : 2/8 = 0.25.

---

## 3. Recommandation d'amis — amis d'amis non déjà amis (LAB 6 Ex.3)

```
Fonction RecommanderAmis(G, u, limite) → Liste<(Entier, Entier)>
    si u ∉ G.adj alors lever Erreur("utilisateur inconnu") fin si

    amisDirects ← G.adj[u]
    // candidats = sommets à distance EXACTEMENT 2 (amis d'amis), via BFS
    candidats ← SommetsADistance(G, u, 2)        // voir GRAPH_pseudocode §3

    suggestions ← Liste vide
    pour chaque c dans candidats faire
        // c n'est ni u ni un ami direct (garanti par distance 2)
        commun ← |amisDirects ∩ G.adj[c]|        // nb d'amis communs (LAB2 Ex.2)
        Ajouter(suggestions, (c, commun))
    fin pour

    Trier(suggestions, clé = (−commun, c))        // amis communs décroissant, id croissant
    si limite ≠ null alors
        suggestions ← PremiersÉléments(suggestions, limite)
    fin si
    retourner suggestions
fin
```

Complexité : un BFS jusqu'à distance 2 ⇒ **O(N + E)**, plus O(degré) par
candidat pour le comptage d'amis communs.

> LAB 6 Ex.3 : `recommend_friends(start_user, max_recommendations)` =
> « friend recommendation based on friends-of-friends not already friends ».
> Le classement par nombre d'amis communs combine LAB 6 Ex.3 (candidats) et
> LAB 2 Ex.2 (score d'amis communs).

---

## 4. Récapitulatif de complexité

| Opération        | Complexité                  | Source            |
|------------------|-----------------------------|-------------------|
| AmisCommuns      | O(min(deg(a), deg(b)))      | LAB 2 Ex.2        |
| Jaccard          | O(deg(a) + deg(b))          | LAB 2 Ex.2        |
| RecommanderAmis  | O(N + E)                    | LAB 6 Ex.3 + L8   |

---

## 5. Cas limites couverts par les tests (`tests/test_recommendation.py`)

* Amis communs : intersection non vide, intersection vide.
* Jaccard : exemple type du lab, union vide ⇒ 0.
* Recommandation : classement par amis communs, exclusion des amis directs et
  de soi-même, `limite`, aucun candidat (pas d'amis-d'amis), utilisateur inconnu.
