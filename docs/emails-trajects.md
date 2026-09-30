# Emails de l'app `trajects` — référence pour le design

Document de référence pour la mise en forme des emails. Il liste les 7 emails que Bana peut
envoyer au sujet des trajets, qui les reçoit, ce qui les déclenche, et **les variables
disponibles dans chaque gabarit**.

- Code d'envoi : `bana/trajects/utils/mail.py` — seul point d'envoi de l'app.
- Gabarits : `bana/trajects/templates/trajects/email/` — une paire `*_subject.txt` /
  `*_message.txt` par email, plus le partial commun `_recap.txt`.
- Les gabarits sont en **texte brut**. Une version HTML devra consommer les mêmes variables.
- Expéditeur : `Bana <contact@bana.mobi>` pour tous, sauf `member_contact` (voir §7).

---

## Variables communes à tous les emails

| Variable | Type | Exemple | Toujours présente ? |
|---|---|---|---|
| `recipient_name` | str | `"Marie D."` | **Non** — vide si le profil n'a ni identité vérifiée ni prénom/nom. Le gabarit écrit alors « Bonjour, » tout court. |
| `trajet_info` | str | `"Rue de la Station 12, Charleroi → École Saint-Joseph, Gosselies"` | Oui |
| `depart_adresse` | str | `"Rue de la Station 12, Charleroi"` | Oui |
| `arrivee_adresse` | str | `"École Saint-Joseph, Gosselies"` | **Non** — vide sur une offre « dans un rayon » |
| `is_simple` | bool | `True` | Oui — `True` = offre dans un rayon, **sans destination** |
| `search_radius_km` | int / None | `14` | Seulement si `is_simple` |
| `groupe_name` | str | `"École Charleroi (matin)"` | **Non** — libellé libre, souvent vide |
| `heure_depart` | str | `"07:45"` | **Non** — chaîne vide si inconnue |
| `heure_arrivee` | str | `"08:20"` | **Non** — chaîne vide si inconnue |
| `children` | list | `[{"label": "Léa M.", "age": 7}]` | **Non** — liste vide possible |
| `dates` | list[str] | `["12/10/2026", "13/10/2026"]` | Oui, format `JJ/MM/AAAA`, triées |
| `dates_count` | int | `3` | Oui |
| `cta_url` | str | `"https://www.bana.mobi/fr/trajets/r%C3%A9servations/"` | Oui |

> **`trajet_info` s'adapte au type de trajet.** Sur une offre dans un rayon (`is_simple=True`)
> il ne contient que l'adresse de départ — pas de flèche, pas de destination. Le design doit
> prévoir les deux formes : « A → B » et « A, dans un rayon de N km ».

---

## 1. `new_reservation_request` — nouvelle demande de réservation

| | |
|---|---|
| **Pour** | le **Yaya** |
| **Déclencheur** | un parent réserve une ou plusieurs dates — `auto_reserve`, `auto_reserve_bulk` |
| **Groupement** | **1 email par trajet**, même si le parent coche 10 dates d'un coup |

Variables propres :

| Variable | Type | Exemple | Note |
|---|---|---|---|
| `counterpart_name` | str | `"Sophie L."` | le **parent** demandeur |
| `counterpart_named` | bool | `True` | `False` → `counterpart_name` vaut le repli `"un parent"` |
| `requested_places` | int | `2` | nombre d'enfants de la demande |

```
Sujet : Sophie L. vous envoie 3 nouvelles demandes de réservation

Bonjour Marie D.,

Sophie L. vous a envoyé 3 demandes de réservation pour votre trajet.

Trajet : Rue de la Station 12, Charleroi → École Saint-Joseph, Gosselies
Groupe : École Charleroi (matin)
Horaires : 07:45 → 08:20
Nombre d'enfant(s) : 2
Enfant(s) : Léa M. (7 ans), Tom M. (9 ans)

Dates demandées :
- 12/10/2026
- 13/10/2026
- 14/10/2026

Acceptez ou refusez ces demandes depuis votre espace Bana :
https://www.bana.mobi/fr/trajets/r%C3%A9servations/
```

**CTA** → `my_reservations`, onglet des demandes reçues.

---

## 2. `reservation_confirmed` — réservation confirmée

| | |
|---|---|
| **Pour** | le **Parent** |
| **Déclencheur** | le yaya accepte — `manage_reservation` (unitaire) ou `manage_reservations_bulk` (groupé) |
| **Groupement** | 1 email par trajet pour tout le lot accepté |

`counterpart_name` = le **yaya** (repli `"un accompagnateur"`). Le bloc « Accompagnateur : »
et la mention « contactez X » n'apparaissent que si `counterpart_named` est vrai.

```
Sujet : Sophie L. a confirmé 3 de vos réservations

Bonjour Marie D.,

Bonne nouvelle ! Sophie L. a confirmé 3 de vos réservations.

Trajet : …
Accompagnateur : Sophie L.

Dates confirmées :
- 12/10/2026
…
Retrouvez le détail et contactez Sophie L. depuis votre espace Bana :
```

**CTA** → `my_reservations`.

---

## 3. `reservation_rejected` — demande non retenue

| | |
|---|---|
| **Pour** | le **Parent** |
| **Déclencheur** | le yaya refuse (`canceled_by='yaya'`), unitaire ou groupé |
| **Groupement** | 1 email par trajet |

Mêmes variables que §2. Ton volontairement non culpabilisant, et le CTA renvoie vers
**d'autres** trajets plutôt que vers celui qui vient d'être refusé.

**CTA** → `my_reservations`.

---

## 4. `reservation_canceled` — demande annulée côté parent

| | |
|---|---|
| **Pour** | le **Yaya** |
| **Déclencheur** | deux cas distincts, voir ci-dessous |
| **Groupement** | 1 email par trajet **et par motif** |

C'est le seul email dont le **message change selon `canceled_by`**. Le design doit prévoir
les trois variantes :

| `canceled_by` | Situation | Message |
|---|---|---|
| `'parent'` | le parent a retiré sa demande (`cancel_reservation`) | « Sophie L. a annulé sa demande de réservation pour votre trajet. » |
| `'auto'` | le parent a confirmé **un autre** accompagnateur ; Bana a libéré les places (cascade dans `_accept_reservation`) | « Sophie L. a confirmé un autre trajet pour cette date. Sa demande a donc été annulée automatiquement et votre place est à nouveau disponible. » |
| `None` | réservation antérieure à l'ajout du champ | formulation neutre, sans attribution |

Variables propres :

| Variable | Type | Exemple |
|---|---|---|
| `canceled_by` | str / None | `'parent'`, `'auto'`, `'yaya'`, `None` |
| `cancel_reason` | str | `"Annulée — le parent a confirmé ailleurs"` — libellé prêt à afficher, aligné sur les badges de l'app |

> `canceled_by` et `cancel_reason` sont présents dans les 4 emails de réservation, mais ne
> portent du sens que dans celui-ci.

**CTA** → `my_reservations`. Le message précise qu'**aucune action n'est requise**.

---

## 5. `help_proposed` — un yaya se signale sur une date

| | |
|---|---|
| **Pour** | le **Parent** |
| **Déclencheur** | `propose_help` — le yaya clique « proposer mon aide » sur une date |
| **Groupement** | unitaire |

| Variable | Type | Exemple |
|---|---|---|
| `yaya_name` | str | `"Sophie L."` (repli `"un accompagnateur"`) |
| `yaya_named` | bool | `True` |

Pas de `requested_places` ni de `canceled_by` ici. `dates` contient **une seule** date.

```
Sujet : Sophie L. est disponible pour votre trajet du 12/10/2026
```

**CTA** → `my_matchings_researched` (les matchings du parent).

---

## 6. `help_proposed_bulk` — un yaya se signale sur plusieurs dates

| | |
|---|---|
| **Pour** | le **Parent** |
| **Déclencheur** | `propose_help_match` — **proposition groupée** : un clic couvre toutes les dates disponibles du groupe de trajets du yaya |
| **Groupement** | 1 seul email pour tout le groupe |

Mêmes variables que §5, mais `dates` contient **toutes** les dates disponibles et non un
simple décompte : le design peut donc les lister.

```
Sujet : Sophie L. est disponible pour 3 dates de votre recherche

Bonne nouvelle ! Sophie L. est disponible pour 3 dates de votre recherche de trajet.
…
Dates disponibles :
- 12/10/2026
- 13/10/2026
- 14/10/2026
```

**CTA** → `my_matchings_researched`.

---

## 7. `member_contact` — message d'un membre à un autre

| | |
|---|---|
| **Pour** | le **Parent ou le Yaya** — l'un des deux côtés d'une réservation confirmée |
| **Déclencheur** | `contact_member` — formulaire de contact, réservé aux abonnés ayant une réservation confirmée en commun, avec quotas horaires |
| **Groupement** | unitaire |

**Cet email sort du modèle commun** :

- **From** : `"Sophie L. via Bana" <contact@bana.mobi>` — l'adresse de service est imposée par
  l'authentification SPF/DKIM OVH, seul le nom affiché change.
- **Reply-To** : l'adresse réelle de l'expéditeur. Le destinataire répond depuis sa boîte et
  la réponse arrive directement, sans repasser par Bana.
- **Pas de CTA** : le mécanisme, c'est la réponse par email.
- ⚠️ **Ne jamais y mettre « ne pas répondre à cet email »** — le message dit explicitement
  l'inverse.

| Variable | Type | Exemple |
|---|---|---|
| `recipient_name` | str | `"Marie D."` |
| `sender_name` | str | `"Sophie L."` (repli `"Un membre"`) |
| `context_label` | str | `"École Charleroi (matin)"` — **souvent vide** |
| `body` | str | texte libre, jusqu'à 2000 caractères, **sauts de ligne inclus** |

`body` est du contenu écrit par un utilisateur : le design doit prévoir un bloc de citation
qui encaisse un texte long, multi-lignes, sans mise en forme.

---

## Cas de figure à prévoir dans le design

Chacun se produit avec des données réelles :

1. **1 date vs N dates** — tous les emails basculent sur `dates_count`. Les actions groupées
   (réserver 10 dates, accepter tout un lot) produisent **un seul** email, pas dix.
2. **Trajet sans destination** — `is_simple=True` : afficher « Départ : X (dans un rayon de
   N km) » et non « X → ».
3. **`groupe_name` vide** — masquer la ligne, ne pas afficher d'étiquette orpheline.
4. **Horaires inconnus** — `heure_depart` et `heure_arrivee` peuvent être vides
   indépendamment l'un de l'autre. Masquer la ligne si les deux le sont.
5. **Aucun enfant rattaché** — `children` vide.
6. **Interlocuteur anonyme** — profil sans identité vérifiée ni prénom/nom : `counterpart_name`
   vaut `"un parent"` / `"un accompagnateur"` en **minuscules**, et `counterpart_named` est
   `False`. Les gabarits texte appliquent `|capfirst` en tête de phrase ; une version HTML
   devra faire pareil, et masquer les tournures du type « Accompagnateur : ».
7. **Destinataire anonyme** — `recipient_name` vide : « Bonjour, » sans nom.
8. **Adresses très longues** — `start_adress` / `end_adress` font jusqu'à 255 caractères
   chacune. `trajet_info` peut donc dépasser 500 caractères : ne pas le mettre tel quel dans
   un objet d'email ou un titre sans troncature.

---

## Pied de page (à ajouter, non implémenté)

Aucun email n'a de pied de page aujourd'hui. Le minimum légal belge et RGPD à prévoir dans le
design :

- Dénomination sociale, adresse du siège, **numéro d'entreprise BCE** (à récupérer dans
  `mentions-legales-bana.pdf` — absent du code)
- `contact@bana.mobi` · `+32 495 283 791`
- Raison de l'envoi (« Vous recevez cet email parce que vous avez un compte Bana »)
- Liens CGU · Confidentialité · Mentions légales · Cookies
- Lien « gérer mes notifications »

---

## Notes techniques

- **URLs** : construites par `absolute_url()` (`trajects/utils/display.py`) à partir du
  réglage `SITE_BASE_URL`. Les routes sont sous `i18n_patterns(prefix_default_language=True)`,
  donc **toujours préfixées `/fr/`**. `my_reservations` s'encode en
  `/fr/trajets/r%C3%A9servations/` (accent dans le pattern).
- **Pas de page de détail** : il n'existe aucune route consultable par réservation ou par
  trajet, et les actions (accepter, refuser, annuler, contacter) sont toutes en POST. Le seul
  CTA possible est la page `my_reservations` ou la page de matchings — pas de deep link vers
  une réservation précise, ni de bouton « accepter » directement dans l'email.
- **Traductions** : les gabarits sont en français en dur, sans `{% trans %}`. `LANGUAGES` ne
  déclare que `fr` pour l'instant.
