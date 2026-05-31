# Pseudo-code — Gate Timeline (score de proximité + MergeSort)

> Sources, aucune procédure inventée :
> **Sujet ASNAP / Social Gate, slide 6** (« Score post Calculation » : 1 like
> d'un ami = 10 points, 1 like d'un inconnu = 1 point) ; **LAB 4 Ex.2**
> (`merge_sort_by_engagement`, Divide & Conquer) et **Lecture 9** (Merge Sort :
> diviser en moitiés, conquérir récursivement, fusionner, O(n log n)) ;
> notion d'« ami » = voisin direct du graphe (distance 1, Lecture 8 / LAB 6).
> Le poids par type de like est dans l'esprit du `engagement_score` pondéré de
> **LAB 3 Ex.3** (likes/commentaires/partages avec poids différents).
> Conventions de pseudo-code : règles de **Lecture 2, slides 10-18**.

---

## 1. Score de proximité d'un post (sujet ASNAP slide 6)

```
Fonction ScoreProximité(post, observateur, G) → Entier
    score ← 0
    pour chaque likeur dans post.likes faire
        si SontAmis(G, observateur, likeur) alors
            score ← score + 10           // like d'un ami
        sinon
            score ← score + 1            // like d'un inconnu
        fin si
    fin pour
    retourner score
fin // O(L), L = nombre de likes (SontAmis en O(1) moyen sur la liste d'adjacence)
```

Le score dépend de **l'observateur** : un même post n'a pas le même score selon
qui regarde sa timeline (les amis ne sont pas les mêmes).

---

## 2. MergeSort — notre propre tri (LAB 4 Ex.2 / Lecture 9)

```
Fonction TriFusion(L, clé, décroissant) → Liste
    si |L| ≤ 1 alors retourner Copie(L) fin si      // cas de base
    milieu ← |L| div 2
    gauche ← TriFusion(L[0 .. milieu-1], clé, décroissant)   // diviser
    droite ← TriFusion(L[milieu .. |L|-1], clé, décroissant)
    retourner Fusion(gauche, droite, clé, décroissant)       // fusionner
fin // O(n log n), stable

Fonction Fusion(g, d, clé, décroissant) → Liste
    résultat ← Liste vide ; i ← 0 ; j ← 0
    tant que i < |g| et j < |d| faire
        si décroissant alors prendreGauche ← (clé(g[i]) ≥ clé(d[j]))
        sinon                 prendreGauche ← (clé(g[i]) ≤ clé(d[j]))
        fin si
        si prendreGauche alors Ajouter(résultat, g[i]) ; i ← i+1
        sinon                  Ajouter(résultat, d[j]) ; j ← j+1
        fin si
    fin tant que
    Ajouter tous les restes de g (depuis i) puis de d (depuis j)
    retourner résultat
fin
```

> Diviser pour régner (Lecture 9) : on coupe en deux moitiés, on trie chacune
> récursivement, puis on fusionne deux listes déjà triées en temps linéaire.
> Stable : à clé égale, l'élément de gauche passe d'abord.

---

## 3. Classement de la timeline

```
Fonction ClasserTimeline(posts, observateur, G) → Liste<(post, score)>
    scorés ← [ (p, ScoreProximité(p, observateur, G)) pour p dans posts ]
    // 1er passage stable : plus récent d'abord (id décroissant)
    parRécence ← TriFusion(scorés, clé = (p,s) ⟹ p.post_id, décroissant = Vrai)
    // 2e passage stable : score décroissant ; à score égal, récence conservée
    retourner TriFusion(parRécence, clé = (p,s) ⟹ s, décroissant = Vrai)
fin // O(P·L̄ + P log P)
```

> Deux passages de tri stable = tri multi-critères : score décroissant en
> priorité, puis (à égalité) le plus récent d'abord. Aucun tri de bibliothèque
> n'est utilisé — c'est `TriFusion` (notre code) partout, comme l'exige ASNAP.

---

## 4. Récapitulatif de complexité

| Opération          | Complexité     | Source              |
|--------------------|----------------|---------------------|
| ScoreProximité     | O(L)           | Sujet slide 6       |
| TriFusion (MergeSort) | O(n log n)  | LAB 4 Ex.2 / L9     |
| ClasserTimeline    | O(P·L̄ + P log P) | combinaison        |

---

## 5. Cas limites couverts par les tests (`tests/test_feed.py`, `test_posts.py`)

* MergeSort : liste vide, singleton, ascendant, descendant, **stabilité**,
  comparaison avec le tri de référence sur entrée aléatoire.
* Score : like d'ami = 10 / inconnu = 1, que des inconnus, aucun like = 0.
* Classement : tri par score décroissant, égalité ⇒ plus récent d'abord.
* Posts : contenu vide rejeté, contenu trop long rejeté, like idempotent,
  unlike, post inconnu, round-trip de persistance (next_id conservé).
