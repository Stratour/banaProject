# Brief UX/UI — Refonte de l'interface « Trajets »
> Document destiné à **Claude Design** pour un premier jet visuel.
> Produit le 2026-06-23 à partir de l'analyse du code source (21 templates, vues, formulaires).

---

## 0. Introduction & principes directeurs

### Objectif
Refondre l'interface des « Trajets » de BanaCommunity pour qu'elle soit **claire, sans friction et fluide**. Les utilisateurs (parents et yayas) doivent pouvoir saisir toutes leurs données sans se perdre, comprendre immédiatement où ils en sont, et voir les résultats de leurs actions.

### 4 principes mesurables

| Principe | Définition |
|---|---|
| **Clarté** | L'utilisateur sait toujours sur quel écran il est, ce qu'il s'apprête à créer, et quel sera le résultat |
| **Saisie sans friction** | Chaque champ est explicite, les erreurs sont prévisibles, aucune action n'est silencieuse |
| **Feedback immédiat** | Toute action (sélection de jour, changement de motif, soumission) produit une réponse visible instantanée |
| **Fluidité HTMX** | Navigations, onglets et actions secondaires se font sans rechargement de page complet |

### Design system à conserver
- **Couleur de marque :** `#007F73` (classes Tailwind : `brand`, `brand-50`, `brand-dark`)
- **Cartes :** `rounded-2xl border border-gray-200 bg-white shadow-sm`
- **Badges de statut :** jaune = en attente · vert = confirmé · rouge = annulé
- **JS :** vanilla uniquement (pas de React/Vue)
- **Modals :** élément natif `<dialog>`
- **HTMX :** déjà en place côté réservations — modèle à étendre

---

## 1. Vue d'ensemble — les 4 parties

### Modèle mental

```
                         ┌─────────────────────────────────┐
                         │       MOTEUR DE MATCHING        │
                         │  PostGIS 50 km → rayon → modes  │
                         │  → ±45 min → places disponibles │
                         └──────────────┬──────────────────┘
                                        │
            ┌───────────────────────────┴───────────────────────────┐
            ▼                                                       ▼
  ┌──────────────────┐                                   ┌──────────────────┐
  │  YAYA (offres)   │                                   │  PARENT (demandes)│
  ├──────────────────┤                                   ├──────────────────┤
  │ Proposer A → B   │  ◄─────── matching ───────────►  │ Rechercher trajet│
  │ is_simple=False  │                                   │ ResearchedTraject│
  ├──────────────────┤                                   └──────────────────┘
  │ Proposer (rayon) │                                            │
  │ is_simple=True   │  ◄─────── matching ────────────────────────┘
  └──────────────────┘
            │
            └──────────────── RÉSERVATIONS ────────────────────────►
                           Reservation (pending → confirmed/canceled)
```

### Tableau récapitulatif

| Partie | Qui | Rôle | Modèle backend |
|---|---|---|---|
| **Proposer un trajet A→B** | Yaya / Parent | Offre précise départ → arrivée avec horaires | `ProposedTraject` (`is_simple=False`) |
| **Proposer un trajet rayon** | Yaya | Offre sans destination fixe — disponible dans un rayon N km | `ProposedTraject` (`is_simple=True`) |
| **Rechercher un trajet** | Parent | Demande de transport/garde pour ses enfants | `ResearchedTraject` |
| **Mes réservations** | Parent + Yaya | Cycle de réservation : demande → confirmation | `Reservation` |

### Notion de groupe (`groupe_uid`)
Chaque création génère un **`groupe_uid`** (UUID) qui regroupe toutes les occurrences récurrentes d'un même trajet (ex : les 12 lundis de septembre à décembre). L'interface doit toujours présenter **le groupe comme unité principale** et les dates individuelles comme détail dépliable.

### Navigation — 3 onglets partagés

Les parties Proposition, Proposition Rayon et Recherche partagent exactement la même navigation à 3 onglets :

```
[ Nouveau trajet ]  [ Mes trajets ]  [ Mes matchings ]
```

C'est une opportunité de factoriser ce composant et d'uniformiser les comportements.

---

## 2. Récapitulatif écran par écran

### 2.1 Proposition (A→B) — `proposition/`

#### `creer.html` — Formulaire de création
- **But :** Créer une offre de covoiturage précise avec départ, arrivée, horaires et récurrence.
- **Blocs UI actuels :**
  - Étape 1 : Nom du trajet + adresse de départ (autocomplétion) + heure + adresse d'arrivée + heure
  - Étape 2 : Sélecteur de jours + récurrence + dates + modes de transport
  - Étape 3 : Nombre de places + notes
- **Actions :** Soumission `POST` → crée N occurrences liées par `groupe_uid`
- **Type :** Page complète (pas de fragment HTMX)

#### `trajets_liste.html` — Mes trajets
- **But :** Liste de tous les groupes de trajets proposés par l'utilisateur.
- **Blocs UI :** Cartes par groupe — nom, plage de dates, départ, arrivée, transport, bouton « Voir les dates » → detail, bouton supprimer (modal de confirmation)
- **Données :** Nom du groupe, `date_debut` → `date_fin`, adresses, heures, modes de transport
- **Actions :** Accéder au détail, supprimer un groupe

#### `trajet_detail.html` — Détail d'un groupe
- **But :** Lister toutes les occurrences (dates) d'un groupe, distinguer à venir / passées.
- **Blocs UI :** En-tête groupe (même que carte liste) + section « Dates à venir » (dates + places + supprimer) + section « Dates passées » (grisées, suppression désactivée)
- **Données :** Dates formatées, places disponibles par occurrence
- **Actions :** Supprimer une occurrence individuelle

#### `matchings.html` — Mes matchings
- **But :** Voir quels parents ont un trajet qui correspond aux offres de l'utilisateur.
- **Blocs UI :** Cartes par groupe + sous-section « Matchings trouvés » : avatar, nom, plage de dates, bouton « Voir les dates »
- **Gate :** Si non abonné → nom en rouge « Abonnement requis »
- **Actions :** Accéder au détail d'un matching

#### `matching_detail.html` — Détail d'un matching
- **But :** Vue date par date d'un matching spécifique avec un parent.
- **Blocs UI :**
  - Carte profil du parent (avatar, nom, rôle, dates)
  - Grille méta (départ/arrivée/transport)
  - Section enfants (boutons cliquables → modal détail enfant : âge, siège, handicap, langues, besoins spéciaux)
  - Liste de dates disponibles avec statut et action
- **Statuts/actions par date :**
  - Date passée → badge gris « Date passée »
  - Confirmée → badge vert « Confirmé »
  - En attente → badge jaune « En attente »
  - Disponible → bouton « Proposer mon aide » (`POST` → `propose_help`)
  - Non vérifié → badge amber « Complétez votre vérification »
- **Type :** Plein écran + fragment HTMX si `request.htmx`

---

### 2.2 Proposition Rayon — `proposition_rayon/`

Identique à Proposition A→B **sauf** :
- **Formulaire :** Pas d'adresse d'arrivée — remplacée par un **rayon de recherche (km)** (1–50)
- **Pas d'horaires dans le matching** (offre flexible, sans destination fixe)
- **Liste/détail :** Affiche « Ville X dans un rayon de Y km » au lieu de l'adresse d'arrivée
- **Matching :** Distance seule (≤ rayon), aucune vérification d'horaires ni d'arrivée

---

### 2.3 Recherche (Parent) — `recherche/`

Miroir des propositions du point de vue parent.

#### `creer.html` — Formulaire de recherche
- **But :** Le parent décrit le trajet dont il a besoin pour ses enfants.
- **Blocs UI :**
  - Étape 1 : Nom + départ (autocomplétion) + heure + arrivée + heure
  - Étape 2 : Jours + récurrence + dates + modes de transport
  - Étape 3 : Sélection des enfants (cases à cocher parmi les enfants pré-enregistrés)
- **Prérequis :** L'utilisateur doit avoir au moins un enfant enregistré dans son profil

#### `trajets_liste.html` / `trajet_detail.html`
- Identiques à Proposition A→B mais affichent les **enfants** à la place du nombre de places

#### `matchings.html` / `matching_detail.html`
- **But :** Voir les yayas qui correspondent à la demande du parent.
- **Action principale :** Bouton « Réserver » (`POST` → `auto_reserve`) — gate : abonnement complet + vérification identité + photo
- **Statuts :** Confirmé (vert) · En attente (jaune) · Annulé (rouge)

---

### 2.4 Réservations — `reservation/`

#### `trajets_liste.html` + `partials/reservations_content.html` (HTMX)
- **But :** Hub central de gestion des réservations — double vue selon le rôle.
- **Navigation :** 2 onglets HTMX (À venir / Historique) avec compteurs

**Vue Parent — « Réservations effectuées »**
- Groupées par `(proposed_groupe_uid, yaya_id)` → accordéon : en-tête Yaya + sous-tableau des dates
- Colonnes : Date · Heure · Enfants (boutons → modal) · Places · Statut
- Pagination HTMX (`?tab=&made_page=`)

**Vue Yaya — « Demandes reçues »**
- Groupées par `proposed_groupe_uid` → 1 carte par trajet avec compteurs (en attente / dates pleines / dates disponibles)
- Bouton « Voir les demandes » → `recues_detail.html`
- Pagination HTMX (`?tab=&received_page=`)

#### `recues_detail.html` — Détail des demandes reçues (Yaya)
- **But :** Yaya confirme ou refuse chaque réservation par parent et par date.
- **Structure :** En-tête trajet + blocs par parent (mini profil + sous-tableau)
- **Colonnes :** Date · Enfants · Places restantes · Statut
- **Actions par ligne :**
  - Pending → boutons « Confirmer » (vert) / « Refuser » (rouge)
  - Confirmé → badge vert
  - Annulé → badge rouge
- **Retour :** Lien « ← Retour » avec préservation du tab (`?tab=active`)

---

## 3. Réservations — cycle de vie

```
                  [Parent] auto_reserve
                         │
                         ▼
                    ┌─────────┐
                    │ PENDING │ ──── email → Yaya (« Nouvelle demande »)
                    └────┬────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
     ┌─────────────┐           ┌──────────┐
     │  CONFIRMED  │           │ CANCELED │
     │  (accept)   │           │ (reject) │
     └─────────────┘           └──────────┘
   email → Parent            email → Parent
   places décrémentées
   user ajouté à confirmed_users
```

**Règles :** confirmed et canceled sont terminaux · La Yaya ne peut rejeter une réservation confirmée · `number_of_places` est décrémenté à la confirmation (jamais en dessous de 0).

---

## 4. Audit UX/UI — Problèmes & Recommandations

### P1 — Formulaires de création longs et sans repère de progression

**Problème :** Les 3 `creer.html` utilisent le même layout « grande icône à gauche + champs à droite » répété 3 fois, séparé par des `<hr>`. Sur mobile, l'utilisateur doit scroller longuement sans savoir combien d'étapes restent.

**Impact :** L'utilisateur ne sait pas où il en est, risque d'abandon, erreurs en bas de formulaire non vues.

**Recommandation :**
- Remplacer par un **stepper horizontal en 3 étapes** avec barre de progression (`Trajet → Quand → Détails`), étapes clairement numérotées.
- Sur mobile : **bouton « Suivant »** entre chaque étape (formulaire en plusieurs passes) + bouton « Enregistrer » sticky en bas.
- Sur desktop : formulaire condensé sur une seule page avec sections compactes titrées.

```
Desktop :
┌───────────────────────────────────────────────┐
│  ① Trajet        ② Quand         ③ Détails   │
│  ──────────  ───────────────  ──────────────  │
│                                               │
│  [champs départ / arrivée]                    │
│                                               │
│  [widget calendrier]                          │
│                                               │
│  [places / notes]                [Enregistrer]│
└───────────────────────────────────────────────┘

Mobile :
┌────────────────────────┐
│  ① Trajet  ②  ③        │  ← stepper
│  ──────────            │
│                        │
│  [champs départ]       │
│  [champs arrivée]      │
│                        │
│  [  Suivant →  ]       │  ← sticky
└────────────────────────┘
```

---

### P2 — Widget récurrence/calendrier confus (voir §5 pour le détail)

**Problème :** L'utilisateur ne voit pas quelles dates réelles seront créées. Vocabulaire abstrait (« bi-hebdomadaire »). Champ `date_fin` qui apparaît/disparaît de façon imprévisible.

**Impact majeur :** Erreurs de saisie fréquentes, incompréhension du résultat, perte de confiance.

→ Voir **§5** pour la refonte détaillée du composant.

---

### P3 — `reservations_content.html` monolithique

**Problème :** Le fichier gère 4 états imbriqués (Parent vs Yaya × À venir vs Historique) en un seul template très long.

**Impact :** Difficile à maintenir, comportement difficile à tester, risque d'afficher la mauvaise vue.

**Recommandation :** Découper en 4 sous-partials inclus conditionnellement :
- `partials/made_active.html`, `partials/made_history.html`
- `partials/received_active.html`, `partials/received_history.html`

---

### P4 — Modals « détail enfant » dupliqués

**Problème :** Le même code de modal (nom, âge, siège enfant, handicap, langues, besoins spéciaux) est copié-collé dans `matching_detail.html`, `recues_detail.html` et `reservations_content.html`.

**Impact :** Toute modification doit être faite 3× ; risque d'incohérence visuelle.

**Recommandation :** Créer un partial unique `partials/child_modal.html` inclus avec `{% include ... with child=child %}`.

---

### P5 — Badges de statut répétés dans 5+ templates

**Problème :** La logique `{% if status == 'confirmed' %}...{% elif status == 'pending' %}...` est écrite 5 fois avec des classes légèrement différentes.

**Recommandation :** Créer un inclusion tag `{% status_badge reservation %}` ou un partial `partials/status_badge.html` avec un seul dictionnaire de classes par statut.

---

### P6 — Saisie d'adresse sans feedback d'erreur clair

**Problème :** L'autocomplétion utilise un champ caché `place_id`. Si l'utilisateur tape une adresse sans sélectionner une suggestion, le champ caché reste vide → la validation échoue côté serveur avec un message générique, l'utilisateur ne comprend pas pourquoi.

**Impact :** Frustration, rechargement de page, perte des autres données saisies.

**Recommandations :**
1. Afficher un message d'aide sous le champ dès le focus : *« Commencez à taper puis choisissez une adresse dans la liste »*
2. Valider côté client (JS vanilla) avant soumission : si `place_id` vide → bloquer et surligner le champ
3. Proposer les **adresses favorites** (`fav_addresses`) comme raccourcis cliquables sous le champ (déjà disponibles via `json_script` dans les templates)

```
┌──────────────────────────────────────────┐
│ 📍 Rue de la Loi, Bruxelles         [×] │
│ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ │
│  Adresses favorites :                    │
│  ⭐ Maison     ⭐ École Jules Ferry       │
└──────────────────────────────────────────┘
```

---

### P7 — Gardes abonnement/vérification hétérogènes

**Problème :** Les messages de restriction apparaissent sous 3 formes différentes selon le template :
- Texte rouge inline « Abonnement requis »
- Badge amber « Complétez votre vérification pour réserver »
- Badge vert « Abonnez-vous pour réserver »

**Impact :** Confusion sur ce qui est requis exactement, hiérarchie visuelle incohérente.

**Recommandation :** Définir 2 états clairs avec des composants visuels uniformes :
- **Abonnement manquant** → badge avec icône + lien CTA « Voir les abonnements »
- **Vérification manquante** → badge avec étapes manquantes + lien CTA « Compléter mon profil »

---

### P8 — Accessibilité

**Problèmes constatés :**
- Modals déclenchées via `onclick="document.getElementById('...').showModal()"` sans gestion du focus clavier
- Boutons icônes sans `aria-label`
- Pastilles de jours (L M M J V S D) sans label accessible

**Recommandations :**
- Ajouter `aria-label` sur tous les boutons icônes
- Gérer le retour du focus à la fermeture des modals
- Pastilles jours : utiliser `<label>` wrappant un `<input type="checkbox">` (déjà le cas — OK) + ajouter le nom complet du jour en `title`

---

### P9 — Cohérence inter-parcours (3 formulaires quasi identiques)

**Problème :** Les 3 `creer.html` (proposition / proposition_rayon / recherche) partagent 80 % du même code mais sont des fichiers séparés. Toute modification doit être faite 3×.

**Recommandation à long terme :** Factoriser en partials communs :
- `partials/form_adresses.html` (départ + arrivée ou départ + rayon)
- `partials/form_calendrier.html` (widget récurrence — cf §5)
- `partials/form_details.html` (places / enfants / notes selon le type)

---

## 5. Refonte du widget récurrence/calendrier

> **C'est le point le plus critique de la refonte.** C'est là que les utilisateurs se perdent le plus.

### Widget actuel — ce qui ne marche pas

```
[Lun] [Mar] [Mer] [Jeu] [Ven] [Sam] [Dim]   ← pastilles (pas de lien avec des dates réelles)

Récurrence :
○ Unique
○ Hebdomadaire
○ Bi-hebdomadaire   ← mot abstrait
○ Une semaine

Date de début : [____-__-__]
Date de fin :   [____-__-__]   ← apparaît/disparaît en JS, désorientation
```

**Problèmes :**
1. L'utilisateur ne voit jamais **quelles dates seront réellement créées**
2. « Bi-hebdomadaire » = mot technique incompris
3. `date_fin` qui apparaît/disparaît sans explication
4. Aucun feedback sur le nombre de trajets qui seront créés
5. Sur mobile, les 7 pastilles dépassent parfois en largeur

---

### Proposition — Widget calendrier autonome

#### Contrat backend (à respecter)
Le serveur Django attend ces 4 champs — le widget doit les soumettre inchangés :
- `recurrence_type` : `"one_week"` | `"weekly"` | `"biweekly"`
- `date_debut` : date ISO
- `date_fin` : date ISO (requise si weekly/biweekly)
- `tr_weekdays` : liste de valeurs 1–7 (1=lundi … 7=dimanche)

#### Wireframe ASCII du nouveau widget

```
┌─────────────────────────────────────────────────────────────┐
│  📅  Quand proposez-vous ce trajet ?                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Motif de récurrence                                        │
│  ┌───────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ Une fois  │  │ Chaque semaine │  │ Une semaine sur 2  │ │  ← remplace les radio boutons
│  │  (unique) │  │   (weekly)     │  │   (biweekly)       │ │    + "une semaine" dans la plage
│  └───────────┘  └────────────────┘  └────────────────────┘ │
│                                                             │
│  Jours (sélectionnez au moins un)                          │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐              │
│  │ L │ │ M │ │ M │ │ J │ │ V │ │ S │ │ D │              │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘              │
│                                                             │
│  Plage de dates                                             │
│  Du [23/06/2026] au [30/06/2026]                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ← Juin 2026 →                                             │
│  L   M   M   J   V   S   D                                │
│  1   2   3   4   5   6   7                                │
│  8   9  10  11  12  13  14                                │
│ 15  16  17  18  19  20  21                                │
│ 22 [23] 24  25  26  27  28                                │  ← [23] = début sélectionné
│ [29][30]  1   2   3   4   5                               │  ← [29][30] = occurrences surlignées
├─────────────────────────────────────────────────────────────┤
│  ✅  2 trajets seront créés : lundi 29 juin, mardi 30 juin │  ← récap dynamique
└─────────────────────────────────────────────────────────────┘
```

#### États du widget

| État | Description |
|---|---|
| **Vide** | Motif non choisi · Pastilles jours grises · Calendrier affiché mais sans sélection |
| **Motif choisi** | Carte active surlignée · Pastilles activables · Champs de dates affichés |
| **Jours + dates sélectionnés** | Calendrier surligne toutes les occurrences générées en brand color |
| **Récap** | Barre en bas : « N trajets seront créés : [liste des dates] » |
| **Erreur** | Border rouge sur le champ invalide + message explicite juste en dessous |

#### Règles d'affichage selon le motif

| Motif | `date_debut` | `date_fin` | Jours | Calendrier |
|---|---|---|---|---|
| « Une fois » | Requis (un seul jour dans le calendrier) | Masqué | Masqué (1 jour = 1 clic sur le calendrier) | Sélection d'un seul jour |
| « Chaque semaine » | Requis | Requis | Requis | Surligne chaque semaine les jours choisis |
| « Une semaine sur 2 » | Requis | Requis | Requis | Surligne toutes les 2 semaines |
| *(anciennement « Une semaine »)* | Implicite via sélection plage | Implicite | Requis | Surligne dans la plage (max 7 jours) |

> **Note :** Pour « Une fois », l'utilisateur clique directement une date dans le calendrier → `date_debut = date_fin = date choisie`, `recurrence_type = "one_week"`, `tr_weekdays = [jour_de_la_semaine]`.

#### Comportement « Une semaine précise »
Le motif « one_week » (plage ≤ 7 jours) peut être rendu plus intuitif en le fusionnant avec la sélection calendrier : l'utilisateur clique-glisse (ou clique début puis fin) pour sélectionner une plage de dates, et coche les jours dans la sélection. Raccourci clair : *« Cette semaine »* pré-remplit lundi–vendredi de la semaine courante.

#### Récap dynamique (JS vanilla)
Le compteur en bas recalcule à chaque changement :
```
✅ 8 trajets seront créés
   Lun 01 sep · Mer 03 sep · Lun 08 sep · Mer 10 sep …
```
Si la liste dépasse 5 dates : afficher les 5 premières + « … et 3 autres ».

#### Responsive
- **Desktop :** Calendrier pleine largeur + récap sur la même ligne
- **Mobile :** Calendrier prend toute la largeur · Pastilles jours sur 2 lignes si nécessaire · Récap fixé en bas de l'écran (sticky)

#### Accessibilité
- Pastilles jours : `<label>` wrappant `<input type="checkbox" name="tr_weekdays" value="1">` avec `title="Lundi"` et `aria-label="Lundi"`
- Jours du calendrier : `<button type="button" aria-label="23 juin 2026" aria-pressed="true/false">`
- Motifs récurrence : `<button role="radio" aria-checked="true/false">`
- Navigation calendrier (← →) : `aria-label="Mois précédent"` / `aria-label="Mois suivant"`

---

## 6. Pistes de fluidité HTMX (optionnel)

Le modèle HTMX est déjà en place pour les réservations. Voici les extensions à envisager, par ordre de priorité :

### Priorité haute — Onglets Nouveau/Mes trajets/Mes matchings

Actuellement : navigation classique (rechargement de page complet).

```html
<!-- Pattern à appliquer (identique aux onglets réservations existants) -->
<a hx-get="{% url 'my_proposed_trajects' %}"
   hx-target="#trajet-content"
   hx-swap="outerHTML"
   hx-push-url="true">
  Mes trajets
</a>
```

Avantage : la sidebar et le header ne rechargent pas, transition perçue instantanée.

### Priorité haute — Actions « Proposer mon aide » / « Réserver »

Actuellement : `POST` classique → rechargement complet de la page.

**Proposé :** `hx-post` + `hx-target` sur la ligne concernée → remplace uniquement le badge de statut de la ligne sans recharger toute la liste de dates.

```
Avant (rechargement) : [Proposer mon aide] → POST → 302 → rechargement
Après (HTMX)        : [Proposer mon aide] → hx-post → renvoie le badge HTML → swap
```

### Priorité moyenne — Validation inline du formulaire

Valider les champs `date_debut` / `date_fin` / `tr_weekdays` au `blur` (ou onchange) via `hx-post` → retourne un fragment `<p class="text-red-600">` si invalide, `""` si valide. L'utilisateur voit les erreurs **avant** de soumettre.

### Priorité basse — Aperçu calendrier côté serveur

Option avancée : déléguer le calcul des dates au serveur via `hx-get` pour avoir une source de vérité unique utilisant `generate_recurrent_dates()` (au lieu de re-implémenter la logique en JS vanilla côté client). Utile si la logique de récurrence devient plus complexe.

---

## 7. Annexe — Cartographie écrans ↔ URLs ↔ vues

### Proposition A→B

| Écran | URL name | Vue | Template |
|---|---|---|---|
| Créer | `proposed_traject` | `proposed_traject` | `proposition/creer.html` |
| Mes trajets | `my_proposed_trajects` | `my_proposed_trajects` | `proposition/trajets_liste.html` |
| Détail groupe | `my_proposed_groupe_detail` | `my_proposed_groupe_detail` | `proposition/trajet_detail.html` |
| Mes matchings | `my_matchings_proposed` | `my_matchings_proposed` | `proposition/matchings.html` |
| Détail matching | `my_matchings_proposed_detail` | `my_matchings_proposed_detail` | `proposition/matching_detail.html` |
| Supprimer groupe | `delete_proposed_groupe` | `delete_proposed_groupe` | — (redirect) |
| Supprimer occurrence | `delete_proposed_traject` | `delete_proposed_traject` | — (redirect) |

### Proposition Rayon

| Écran | URL name | Vue | Template |
|---|---|---|---|
| Créer | `simple_proposed_traject` | `simple_proposed_traject` | `proposition_rayon/creer.html` |
| Mes trajets | `my_simple_trajects` | `my_simple_trajects` | `proposition_rayon/trajets_liste.html` |
| Détail groupe | `my_simple_groupe_detail` | `my_simple_groupe_detail` | `proposition_rayon/trajet_detail.html` |
| Mes matchings | `my_matchings_simple` | `my_matchings_simple` | `proposition_rayon/matchings.html` |
| Détail matching | `my_matchings_simple_detail` | `my_matchings_simple_detail` | `proposition_rayon/matching_detail.html` |

### Recherche (Parent)

| Écran | URL name | Vue | Template |
|---|---|---|---|
| Créer | `researched_traject` | `researched_traject` | `recherche/creer.html` |
| Mes trajets | `my_researched_trajects` | `my_researched_trajects` | `recherche/trajets_liste.html` |
| Détail groupe | `my_researched_groupe_detail` | `my_researched_groupe_detail` | `recherche/trajet_detail.html` |
| Mes matchings | `my_matchings_researched` | `my_matchings_researched` | `recherche/matchings.html` |
| Détail matching | `my_matchings_researched_detail` | `my_matchings_researched_detail` | `recherche/matching_detail.html` |

### Réservations

| Écran | URL name | Vue | Template |
|---|---|---|---|
| Hub réservations | `my_reservations` | `my_reservations` | `reservation/trajets_liste.html` |
| Contenu HTMX | `my_reservations` | `my_reservations` | `reservation/partials/reservations_content.html` |
| Détail demandes reçues | `my_reservations_received_detail` | `my_reservations_received_detail` | `reservation/recues_detail.html` |
| Gérer une réservation | `manage_reservation` | `manage_reservation` | — (redirect) |
| Créer une réservation | `auto_reserve` | `auto_reserve` | — (redirect) |
| Proposer son aide | `propose_help` | `propose_help` | — (redirect) |

### Moteur de matching

| Source | Fonction | Filtre principal |
|---|---|---|
| `ResearchedTraject` (parent) | `find_matches_for_parent_research()` | Rayon 5 km départ + 5 km arrivée + ±45 min |
| `ProposedTraject` `is_simple=False` (yaya A→B) | `find_matches_for_precise_offer()` | Symétrique au dessus |
| `ProposedTraject` `is_simple=True` (yaya rayon) | `find_matches_for_simple_offer()` | Rayon `search_radius_km` départ uniquement — pas d'horaires |

Pré-filtre PostGIS : 50 km (large) → filtres fins Python : rayon exact · intersection modes de transport · places disponibles · fenêtre ±45 min.

---

*Document généré à partir de l'analyse de :*
- *[bana/trajects/views.py](../bana/trajects/views.py) — dont `generate_recurrent_dates` (L830) et `RecurrenceValidationMixin`*
- *[bana/trajects/templates/trajects/](../bana/trajects/templates/trajects/) — 21 templates*
- *[bana/trajects/forms.py](../bana/trajects/forms.py) · [bana/trajects/models.py](../bana/trajects/models.py) · [bana/trajects/urls.py](../bana/trajects/urls.py)*
