# Pseudo-code — Gate Settings (filtres de seuil de confiance)

> Source : **Sujet ASNAP / Social Gate, slide 5 « Gate Settings »**
> (Threshold slider, « 3 friends likes threshold », « Mutual friends
> threshold ») et l'objectif projet « cacher les posts en dessous d'un nombre
> de likes d'amis ». Ce sont des **filtres par seuil** (logique du sujet, pas un
> algorithme du cours) construits sur des primitives du cours :
> `SontAmis` (Lecture 8 / LAB 6) et le comptage d'amis communs (LAB 2 Ex.2).
> Conventions de pseudo-code : règles de **Lecture 2, slides 10-18**.

---

## 1. Comptage de likes d'amis (primitive)

```
Fonction NbLikesAmis(post, observateur, G) → Entier
    n ← 0
    pour chaque likeur dans post.likes faire
        si SontAmis(G, observateur, likeur) alors n ← n + 1 fin si
    fin pour
    retourner n
fin // O(L), SontAmis en O(1) moyen (Lecture 8 / LAB 6)
```

---

## 2. Filtre seuil de confiance sur la timeline (slide 5)

```
Fonction FiltrerParSeuilAmis(classés, observateur, G, seuil) → Liste
    si seuil ≤ 0 alors retourner classés fin si        // pas de filtre
    retourner [ (post, score) ∈ classés
                tel que NbLikesAmis(post, observateur, G) ≥ seuil ]
fin // O(P · L̄), ordre du classement préservé
```

> « Cacher les posts en dessous d'un nombre de likes d'amis » : on garde un post
> seulement si au moins `seuil` de ses likes proviennent d'amis de l'observateur.

---

## 3. Filtre seuil d'amis communs sur les suggestions (slide 5)

```
Fonction FiltrerSuggestionsParAmisCommuns(suggestions, seuil) → Liste
    si seuil ≤ 0 alors retourner suggestions fin si
    retourner [ s ∈ suggestions tel que s.amisCommuns ≥ seuil ]
fin // O(S)
```

> Le nombre d'amis communs de chaque suggestion vient du module de
> recommandation (LAB 2 Ex.2 + LAB 6 Ex.3).

---

## 4. Récapitulatif de complexité

| Opération                        | Complexité  | Source                 |
|----------------------------------|-------------|------------------------|
| NbLikesAmis                      | O(L)        | SontAmis L8/LAB6       |
| FiltrerParSeuilAmis              | O(P · L̄)    | filtre sujet slide 5   |
| FiltrerSuggestionsParAmisCommuns | O(S)        | filtre sujet slide 5   |

> **Honnêteté** : la notion de « seuil de confiance » est une règle du **sujet
> ASNAP** (slide 5), pas un algorithme du cours. Les briques sous-jacentes
> (`SontAmis`, comptage d'amis communs) sont, elles, issues du cours.

---

## 5. Cas limites couverts par les tests (`tests/test_filters.py`)

* Comptage : likes mêlant amis et inconnus, aucun like d'ami.
* Filtre timeline : seuil 0 (tout gardé), seuil 1, seuil 2.
* Filtre suggestions : seuil sur amis communs, seuil 0 (tout gardé).
