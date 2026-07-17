# 02 — Cartographie des Interfaces (UI)
**Projet :** BanaCommunity (bana.mobi)
**Auditeur :** Analyste Fonctionnel Senior — Digit-Up Agency
**Date :** 2026-06-19

---

## 1. Architecture des layouts

Le projet possède **deux bases de templates distinctes** :

| Layout | Fichier | Contexte d'utilisation |
|---|---|---|
| **Vitrine** | `bana/templates/layouts/base.html` | Pages publiques non connectées |
| **App** | `accounts/templates/allauth/layouts/base.html` | Toutes les vues `@login_required` |

Le layout App inclut :
- `admin-header.html` (header app avec dégradé de marque)
- `admin-side-nav.html` (sidebar navigation)
- `admin-bottom-nav.html` (nav mobile bottom)
- `layouts/footer.html` (footer vitrine partagé)
- `layouts/cookie-banner.html` (bannière cookies)

**Framework CSS :** Tailwind CSS (via `django-tailwind`, compilé dans `theme/static/`). Couleur de marque : `#007F73`.
**JS :** Vanilla JavaScript uniquement. HTMX pour les interactions partielles.

---

## 2. Sitemap Fonctionnel

```
/ (/fr/)
├── /fr/contact/                            → contact.html
├── /fr/mission/                            → about.html
├── /fr/comment-ca-marche/                 → work.html
├── /fr/parent/                             → parent.html
├── /fr/devenir-yaya/                       → yaya.html
├── /fr/tarifs/                             → tarifs.html
├── /offline/                               → offline.html
│
├── /fr/accounts/                           [Allauth]
│   ├── /fr/accounts/login/                → account/login.html
│   ├── /fr/accounts/signup/               → account/signup.html
│   ├── /fr/accounts/password/reset/       → account/password_reset.html
│   ├── /fr/accounts/confirm-email/...     → account/email_confirm.html
│   └── /fr/accounts/social/...            [OAuth Google]
│
├── /fr/profil/                             [accounts app]
│   ├── /fr/profil/mes-informations/       → account/profile/profile.html
│   ├── /fr/profil/mes-informations/edit/  → account/profile/profile_edit.html
│   ├── /fr/profil/mes-enfants/            → account/profile/profile_children.html
│   ├── /fr/profil/mes-enfants/ajouter/    → account/profile/profil_add_child.html
│   ├── /fr/profil/mes-adresses/           → account/profile/profile_addresses.html
│   ├── /fr/profil/mes-adresses/ajouter/   → account/profile/profile_add_address.html
│   ├── /fr/profil/utilisateur/<id>/       → account/profile/profile_user.html
│   └── /fr/profil/securité&connexion/     → account/profile/profile_security.html
│
├── /fr/trajets/                            [trajects app]
│   ├── /fr/trajets/propositions/
│   │   ├── nouveaux-trajets/              → trajects/proposition/creer.html
│   │   ├── mes-trajets/                   → trajects/proposition/trajets_liste.html
│   │   ├── mes-trajets/<uuid>/            → trajects/proposition/trajet_detail.html
│   │   ├── matchings/                     → trajects/proposition/matchings.html
│   │   └── matchings/<uuid>/<uuid>/<id>/  → trajects/proposition/matching_detail.html
│   │
│   ├── /fr/trajets/recherches-rayon/
│   │   ├── nouvelles-recherches/          → trajects/proposition_rayon/creer.html
│   │   ├── mes-recherches/                → trajects/proposition_rayon/trajets_liste.html
│   │   ├── mes-recherches/<uuid>/         → trajects/proposition_rayon/trajet_detail.html
│   │   ├── matchings/                     → trajects/proposition_rayon/matchings.html
│   │   └── matchings/<uuid>/<uuid>/<id>/  → trajects/proposition_rayon/matching_detail.html
│   │
│   ├── /fr/trajets/recherches/
│   │   ├── nouvelles-recherches/          → trajects/recherche/creer.html
│   │   ├── mes-recherches/                → trajects/recherche/trajets_liste.html
│   │   ├── mes-recherches/<uuid>/         → trajects/recherche/trajet_detail.html
│   │   ├── matchings/                     → trajects/recherche/matchings.html
│   │   └── matchings/<uuid>/<uuid>/<id>/  → trajects/recherche/matching_detail.html
│   │
│   └── /fr/trajets/réservations/
│       ├── (liste)                         → trajects/reservation/trajets_liste.html
│       └── reçue/<uuid>/                   → trajects/reservation/recues_detail.html
│
├── /fr/chat/chat/                          → chat/index.html
│
├── /fr/profil/abonnement/                  → stripe_sub/subscription.html
│   ├── /fr/profil/abonnement/réussie/      → stripe_sub/payment_successful.html
│   ├── /fr/profil/abonnement/annulé/       → stripe_sub/payment_cancelled.html
│   └── /fr/profil/identité/complete/       → stripe_sub/identity_complete.html
│
├── /fr/bug_tracker/                        [bug_tracker app]
│   ├── /fr/bug_tracker/                    → bug_tracker/bug_list.html
│   ├── /fr/bug_tracker/dashboard/          → bug_tracker/dashboard.html
│   ├── /fr/bug_tracker/create/             → bug_tracker/bug_create.html
│   └── /fr/bug_tracker/<id>/               → bug_tracker/bug_detail.html
│
└── /fr/bana_admin/                         [bana_admin app]
    ├── admin_view                           → bana_admin/admin_view.html
    ├── validate_members                     → bana_admin/validate_members.html
    └── admin/site-stats/                    → bana_admin/site_stats.html
```

---

## 3. Inventaire des templates par catégorie

### 3.1 Pages Vitrine (publiques)

| Template | URL | Type | Héritage | Données contexte |
|---|---|---|---|---|
| `bana/templates/home.html` | `/fr/` | Landing | `layouts/base.html` | `home_benefits`, `home_roles` |
| `bana/templates/about.html` | `/fr/mission/` | Présentation | `layouts/base.html` | `impacts`, `odd_badges`, `stats`, `partners`, `team_members` |
| `bana/templates/work.html` | `/fr/comment-ca-marche/` | Présentation | `layouts/base.html` | `work_benefits`, `work_detail_steps`, `work_journey_steps`, `work_profiles` |
| `bana/templates/parent.html` | `/fr/parent/` | Landing | `layouts/base.html` | `features_search`, `features_share` |
| `bana/templates/yaya.html` | `/fr/devenir-yaya/` | Landing | `layouts/base.html` | `work_profiles`, `yaya_benefits` |
| `bana/templates/tarifs.html` | `/fr/tarifs/` | Tableau | `layouts/base.html` | `parent_packs`, `defraiement_table`, `tarifs_highlights` |
| `bana/templates/contact.html` | `/fr/contact/` | Formulaire statique | `layouts/base.html` | – |
| `bana/templates/offline.html` | `/offline/` | PWA | `layouts/base.html` | – |

### 3.2 Authentification (Allauth + custom)

| Template | Type | Accès |
|---|---|---|
| `account/login.html` | Formulaire login | Public |
| `account/signup.html` | Formulaire inscription | Public |
| `account/password_reset.html` | Formulaire reset | Public |
| `account/email_confirm.html` | Confirmation email | Token URL |
| `account/verification_sent.html` | Info envoi | Public |
| `account/password_reset_from_key.html` | Nouveau MDP | Token URL |
| `socialaccount/login.html` | OAuth | Public |
| `mfa/totp/activate_form.html` | Activation 2FA TOTP | Authentifié |
| `mfa/webauthn/*.html` | WebAuthn | Authentifié |
| `mfa/recovery_codes/*.html` | Codes de récupération | Authentifié |

### 3.3 Profil Utilisateur (app connectée)

| Template | URL | Type | Données contexte |
|---|---|---|---|
| `account/profile/profile.html` | `/profil/mes-informations/` | Dashboard | `profile`, `onboarding_steps`, `onboarding_complete`, `page_title` |
| `account/profile/profile_edit.html` | `/profil/mes-informations/edit/` | Formulaire | `form`, `user_form`, `profile` |
| `account/profile/profile_children.html` | `/profil/mes-enfants/` | Liste | `children`, `page_title` |
| `account/profile/profil_add_child.html` | `/profil/mes-enfants/ajouter-enfant/` | Formulaire | `form`, `children`, `next_url` |
| `account/profile/profile_addresses.html` | `/profil/mes-adresses/` | Liste | `addresses`, `page_title` |
| `account/profile/profile_add_address.html` | `/profil/mes-adresses/ajouter/` | Formulaire | `form`, `mode` |
| `account/profile/profile_user.html` | `/profil/utilisateur/<id>/` | Détail | `user`, `reviews`, `average_rating`, `form`, `is_own_profile`, etc. |
| `account/profile/profile_security.html` | `/profil/securité&connexion/` | Paramètres | `pending_email`, `password_errors`, `page_title` |

**Partials HTMX :**
| Template | Route HTMX | Rôle |
|---|---|---|
| `account/partials/profile_public.html` | `/profil/public/` | Section avis reçus |
| `account/partials/profile_info.html` | `/profil/info/` | Section infos privées |
| `account/partials/email_settings.html` | Inclus dans profile_security | Paramètres email |
| `account/partials/password_settings.html` | Inclus dans profile_security | Paramètres MDP |

### 3.4 Trajets (app connectée)

Chaque sous-répertoire (`proposition/`, `proposition_rayon/`, `recherche/`) suit la même structure :

| Template | Type | Interactions |
|---|---|---|
| `creer.html` | Formulaire multi-étapes | Autocomplete adresse (AJAX + PostGIS), sélection dates/jours, HTMX |
| `trajets_liste.html` | Liste + accordéon | Pagination HTMX, suppression groupe |
| `trajet_detail.html` | Détail groupe | Dates individuelles, statut actif/passé |
| `matchings.html` | Liste matchings | Cartes matchings, HTMX |
| `matching_detail.html` | Détail matching | Boutons réservation/proposition, gestion places |

**Partials trajects :**
| Template | Rôle |
|---|---|
| `partials/tabs_proposition.html` | Navigation onglets proposition fixe |
| `partials/tabs_proposition_rayon.html` | Navigation onglets proposition rayon |
| `partials/tabs_recherche.html` | Navigation onglets recherche |

**Réservations :**
| Template | Type | Données contexte |
|---|---|---|
| `reservation/trajets_liste.html` | Liste (parent + yaya) | Réservations groupées par `(proposed_groupe_uid, yaya_id)` (côté parent) ou par `proposed_groupe_uid` avec annotations (côté yaya) |
| `reservation/recues_detail.html` | Détail réservations reçues | `parents_dict` (groupé par `user_id`), `rows` avec `reservation`, `research`, `remaining_places` |
| `reservation/partials/reservations_content.html` | Partial HTMX | Fragment rechargeable |

### 3.5 Bug Tracker

| Template | Type | HTMX | Accès |
|---|---|---|---|
| `bug_tracker/bug_list.html` | Liste filtrée paginée | Oui (rechargement table) | Authentifié |
| `bug_tracker/dashboard.html` | Dashboard stats | Oui (rechargement stats) | Authentifié |
| `bug_tracker/bug_create.html` | Formulaire création | Oui | Authentifié |
| `bug_tracker/bug_detail.html` | Détail complet | Non | Authentifié |
| `bug_tracker/bug_edit.html` | Formulaire édition | Oui | Authentifié |

**Partials bug_tracker :**
- `partials/bug_table.html` — Table rechargeable via HTMX
- `partials/bug_form.html` — Formulaire création
- `partials/bug_edit_form.html` — Formulaire édition
- `partials/bug_detail_content.html` — Contenu détail
- `partials/bug_status_badge.html` — Badge statut inline
- `partials/bug_assignee.html` — Champ assignation inline
- `partials/comments_section.html` — Section commentaires
- `partials/attachments_section.html` — Section pièces jointes
- `partials/dashboard_stats.html` — Stats dashboard

### 3.6 Stripe Subscription

| Template | Type | Données contexte |
|---|---|---|
| `stripe_sub/subscription.html` | Présentation plan | `status`, `product`, `price`, `product_price`, `active_subscription` |
| `stripe_sub/payment_successful.html` | Confirmation paiement | `product`, `price`, `start_date`, `end_date`, `is_active`, étapes profil |
| `stripe_sub/payment_cancelled.html` | Page annulation | – |
| `stripe_sub/identity_complete.html` | Retour vérification CI | `is_verified`, `first_name`, `last_name` |

### 3.7 Admin (bana_admin)

| Template | Type | Données contexte |
|---|---|---|
| `bana_admin/admin_view.html` | Dashboard global | `profiles` |
| `bana_admin/validate_members.html` | Validation profils | `profiles` |
| `bana_admin/site_stats.html` | Statistiques visites | `period`, `total_visits`, `anonymous_visits`, `authenticated_visits`, `new_members`, `kpis`, `visits` (paginé) |
| `bana_admin/layout/nav_admin.html` | Navigation admin | – |

---

## 4. Composants JavaScript réutilisables

Fichiers JS dans `bana/static/bana/js/` :

| Fichier | Rôle |
|---|---|
| `components/modal.js` | Gestion modale générique |
| `components/toast.js` | Notifications toast |
| `components/carousel.js` | Carrousel images |
| `components/address_autocomplete.js` | Autocomplete adresse (OpenStreetMap) |
| `components/cookie-banner.js` | Bannière cookie (nouveau, non committé) |
| `components/password-strength.js` | Indicateur force MDP (nouveau, non committé) |
| `sw.js` | Service Worker PWA |

---

## 5. Responsive Design

- **Framework** : Tailwind CSS avec breakpoints `sm:`, `md:`, `lg:`, `xl:`
- **Mobile** : Navigation bottom bar (`admin-bottom-nav.html`) + drawer burger pour le header app
- **Desktop** : Sidebar fixe + header pleine largeur avec dégradé de marque
- **PWA** : Installable sur mobile (manifest, service worker, icônes maskable)

---

## 6. Points d'attention UX/UI

| Point | Observation |
|---|---|
| `about copy.html` | Fichier de brouillon présent dans le dépôt (non lié à une URL) |
| URL avec accent | `/profil/securité&connexion/` — contient `&` et un caractère accentué dans l'URL |
| Page chat | Pas de `@login_required` sur la vue index du chat |
| Onboarding | Séquence d'étapes bien pensée mais dépendante de la vérification Stripe Identity |
