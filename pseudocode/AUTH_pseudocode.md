# Pseudo-code — Login feature (Social Gate)

> Toutes les structures de données utilisées proviennent du cours
> *Advanced Algorithms and Programming* (II.2415).
> Conventions de pseudo-code : règles de programmation structurée vues en
> Lecture 2 (Introduction to Advanced Algorithms), slides 10-18.

---

## 1. Structures de données

### 1.1 BST des utilisateurs (clé = `user_id`)

> Référence : Lecture 10 (slides 7–20) et **LAB 8 — Exercice 1**.

```
Type Utilisateur = Record {
    user_id       : Entier
    username      : Chaîne
    email         : Chaîne
    first_name    : Chaîne
    last_name     : Chaîne
    birth_date    : Date
    salt          : Chaîne (hex)
    password_hash : Chaîne (hex)
    created_at    : Horodatage
}

Type NoeudBST = Record {
    cle  : Entier               // user_id
    val  : Utilisateur
    g, d : Pointeur vers NoeudBST
}

Type BST = Pointeur vers NoeudBST
```

### 1.2 Index secondaires (hash maps)

> Référence : LAB 1 Ex.6 (« First Unique Character Finder ») et la question
> finale d'intégration de LAB 8 qui oppose BST et hash map.

```
H_username : HashMap<Chaîne, Entier>     // username (lower) → user_id
H_email    : HashMap<Chaîne, Entier>     // email (lower)    → user_id
H_session  : HashMap<Chaîne, Entier>     // token            → user_id
```

---

## 2. Hash mot de passe (Lecture 3 — type `File` / fonctions de la stdlib)

```
Procédure HashMotDePasse(motDePasse : Chaîne, sel : Chaîne)
                       → (sel : Chaîne, hash : Chaîne)
    si sel = null alors
        sel ← AléatoireHex(16 octets)
    fin si
    octets ← Concaténation(HexVersOctets(sel),
                            EncodeUTF8(motDePasse))
    hash  ← SHA256(octets)
    retourner (sel, HexEncode(hash))
fin // HashMotDePasse


Fonction VérifieMotDePasse(motDePasse : Chaîne,
                           sel : Chaîne,
                           hashAttendu : Chaîne) → Booléen
    (_, candidat) ← HashMotDePasse(motDePasse, sel)
    retourner ComparaisonTempsConstant(candidat, hashAttendu)
fin // VérifieMotDePasse
```

---

## 3. Inscription (`POST /api/register`)

```
Procédure Inscrire(payload : Dictionnaire)
                  → (utilisateur : Utilisateur, token : Chaîne)
    cleaned ← ValiderInscription(payload)            // formats + bornes
    uname_k ← MinusculesEspacesEnlevés(cleaned.username)
    email_k ← MinusculesEspacesEnlevés(cleaned.email)

    si uname_k ∈ H_username alors
        lever DuplicateUserError("username déjà pris")
    fin si
    si email_k ∈ H_email alors
        lever DuplicateUserError("email déjà enregistré")
    fin si

    (sel, hash) ← HashMotDePasse(cleaned.password, null)
    u          ← NouvelUtilisateur(prochain_id,
                                   cleaned, sel, hash,
                                   MaintenantUTC())

    InsererBST(BST, u.user_id, u)                    // O(log n) moy.
    H_username[uname_k] ← u.user_id
    H_email[email_k]    ← u.user_id
    prochain_id         ← prochain_id + 1

    SauvegarderJSON(BST, prochain_id, fichier_db)

    token ← AléatoireHex(32 octets)
    H_session[token] ← u.user_id
    retourner (u, token)
fin // Inscrire
```

Complexité : O(log n) moyen pour l'insertion BST + O(1) moyen pour les
deux index, dominé par la sauvegarde sur disque qui parcourt l'arbre en
in-order, soit O(n).

---

## 4. Connexion (`POST /api/login`)

```
Procédure Connecter(identifiant : Chaîne,
                    motDePasse  : Chaîne)
                  → (utilisateur : Utilisateur, token : Chaîne) ∪ ⟂
    user_id ← H_username[Minuscules(identifiant)]
    si user_id = null alors
        user_id ← H_email[Minuscules(identifiant)]
    fin si
    si user_id = null alors
        retourner ⟂                                   // pas trouvé
    fin si

    u ← RechercherBST(BST, user_id)                   // O(log n) moy.

    si non VérifieMotDePasse(motDePasse, u.salt, u.password_hash) alors
        retourner ⟂                                   // mauvais mdp
    fin si

    token ← AléatoireHex(32 octets)
    H_session[token] ← u.user_id
    retourner (u, token)
fin // Connecter
```

Complexité : O(1) moyen pour les hash maps + O(log n) moyen pour la BST.

---

## 5. Déconnexion (`POST /api/logout`)

```
Procédure Déconnecter(token : Chaîne) → Booléen
    si token ∈ H_session alors
        Supprimer(H_session, token)
        retourner Vrai
    fin si
    retourner Faux
fin // Déconnecter
```

Complexité : O(1) moyen.

---

## 6. Profil courant (`GET /api/me`)

```
Fonction Profil(token : Chaîne) → Utilisateur ∪ ⟂
    user_id ← H_session[token]
    si user_id = null alors
        retourner ⟂
    fin si
    retourner RechercherBST(BST, user_id)            // O(log n) moy.
fin // Profil
```

---

## 7. Persistance (Lecture 3 — type `File`)

```
Procédure SauvegarderJSON(B : BST, prochain_id : Entier, chemin : Chaîne)
    enregistrements ← liste vide
    ParcoursInOrdre(B, λ (cle, val) ⟹
        Ajouter(enregistrements, val))               // O(n)
    Écrire(chemin, EncoderJSON({"next_id"     : prochain_id,
                                 "users"       : enregistrements}))
fin

Procédure ChargerJSON(B : BST, chemin : Chaîne)
    si non Existe(chemin) alors retourner fin si
    data ← DécoderJSON(Lire(chemin))
    prochain_id ← data["next_id"]
    pour chaque enr dans data["users"] faire
        u ← Utilisateur depuis enr
        InsererBST(B, u.user_id, u)
        H_username[Minuscules(u.username)] ← u.user_id
        H_email[Minuscules(u.email)]       ← u.user_id
    fin pour
fin
```

---

## 8. Récapitulatif de complexité

| Opération                       | Moyenne          | Pire cas (arbre dégénéré) |
|---------------------------------|------------------|----------------------------|
| Inscription (sans persistance)  | O(log n)         | O(n)                       |
| Inscription (avec sauvegarde)   | O(n)             | O(n)                       |
| Connexion                       | O(log n)         | O(n)                       |
| Déconnexion                     | O(1)             | O(1)                       |
| Profil (`/me`)                  | O(log n)         | O(n)                       |
| Persistance (chargement/sauv.)  | O(n)             | O(n)                       |

> *Pire cas* : conformément à L10 slide 20, si les insertions arrivent dans
> l'ordre croissant (ex. inscriptions séquentielles sans rééquilibrage), la
> BST devient une chaîne et la hauteur tend vers `n`. Voir le test
> `tests/test_bst.py::BSTDegenerateChainTest`.

---

## 9. Cas limites couverts par les tests

* Inscription avec champ manquant, email invalide, username invalide,
  mot de passe trop court, date de naissance future.
* Inscription en double (username puis email).
* Connexion avec username, avec email, avec mauvais mot de passe.
* Round-trip de persistance (charger une base sauvegardée doit permettre
  de se réauthentifier).
* BST : suppressions des trois cas (feuille / un enfant / deux enfants),
  duplicats rejetés, parcours in-order ascendant après modifications,
  arbre dégénéré.
* Sessions : unicité des tokens sur 2 000 tirages, révocation idempotente.
