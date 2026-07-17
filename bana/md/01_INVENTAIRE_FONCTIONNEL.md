# 01 — Inventaire Fonctionnel
**Projet :** BanaCommunity (bana.mobi)
**Auditeur :** Analyste Fonctionnel Senior — Digit-Up Agency
**Date :** 2026-06-19

---

## 1. App `bana` — Vitrine & Infrastructure

### Rôle métier
Pages publiques (landing, mission, tarifs, comment-ça-marche) + infrastructure transversale (PWA, SEO, i18n).

### Vues
| URL pattern | Fonction | Auth | Description |
|---|---|---|---|
| `/` | `home` | Non | Page d'accueil avec avantages et rôles |
| `/contact/` | `contact` | Non | Page de contact statique |
| `/mission/` | `about` | Non | Présentation équipe, partenaires, ODD ONU |
| `/comment-ca-marche/` | `work` | Non | Explication du fonctionnement étape par étape |
| `/parent/` | `parent` | Non | Landing spécifique parent |
| `/devenir-yaya/` | `yaya` | Non | Landing spécifique Yaya |
| `/tarifs/` | `tarifs` | Non | Grille tarifaire Parent + défraiement Yaya |
| `/manifest.json` | `manifest` | Non | Manifest PWA (JSON) |
| `/sw.js` | `service_worker` | Non | Service Worker PWA |
| `/offline/` | `offline` | Non | Page hors-ligne PWA |
| `/robots.txt` | `robots_txt` | Non | Fichier robots SEO |
| `/sitemap.xml` | Django sitemaps | Non | Sitemap XML |
| `/switch-language/<lang>/` | `switch_language` | Non | Changement de langue avec redirection |

### Fonctionnalités notables
- **PWA complète** : manifest, service worker, page offline, icônes maskable.
- **Internationalisation** : `i18n_patterns` avec préfixe langue obligatoire (`/fr/`, `/en/`, `/nl/`). Webhook Stripe et sélecteur de langue **hors** `i18n_patterns` (correct).
- **SEO** : sitemap dynamique (`StaticViewSitemap`), robots.txt restrictif (bloque tout sauf pages publiques).
- Les vues injectent des données (avantages, profils témoignages, ODD) sous forme de listes Python dans le contexte — pas de base de données.

### Intégrations externes
- `geopy` / OpenStreetMap API (geocoding)
- Google Maps API (autocomplete adresses)

---

## 2. App `accounts` — Profils & Authentification

### Rôle métier
Gestion des comptes utilisateurs, profils étendus, enfants, adresses favorites, avis, vérification d'identité.

### Modèles
| Modèle | Champs clés | Relations |
|---|---|---|
| `Profile` | `user` (O2O User), `profile_picture`, `address`, `ci_is_verified`, `bvm_is_verified`, `prfl_is_verified`, `document_bvm`, `service` (Parent/Yaya), `transport_modes` (JSONField), `bio`, `verified_first_name`, `verified_last_name`, `onboarding_seen` | O2O → User, M2M → Languages |
| `Languages` | `lang_name`, `lang_abbr` | M2M ← Profile, Child |
| `Child` | `chld_user` (FK User), `chld_name`, `chld_surname`, `chld_birthdate`, `chld_gender`, `chld_seat`, `chld_disability`, `chld_special_needs` | FK → User, M2M → Languages |
| `Review` | `reviewer` (FK User), `reviewed_user` (FK User), `rating` (1-5), `comment`, `created_at` | 2x FK → User |
| `FavoriteAddress` | `uid` (UUID, db_index), `user` (FK), `label`, `address`, `place_id`, `point` (PostGIS PointField srid=4326), `created_at` | FK → User |

### Vues
| URL | Fonction | Auth | Méthode |
|---|---|---|---|
| `/profil/mes-informations/` | `profile_view` | Oui | GET |
| `/profil/mes-informations/edit/` | `profile_edit` | Oui | GET/POST |
| `/profil/mes-enfants/` | `profile_children_view` | Oui | GET |
| `/profil/mes-enfants/ajouter-enfant/` | `add_child_view` | Oui | GET/POST |
| `/profil/mes-enfants/supprimer-enfant/<id>/` | `delete_child_view` | Oui | POST |
| `/profil/mes-adresses/` | `profile_addresses` | Oui | GET |
| `/profil/mes-adresses/ajouter-adresses/` | `create_address` | Oui | GET/POST |
| `/profil/mes-adresses/<uuid>/supprimer-adresse/` | `delete_address` | Oui | POST |
| `/profil/utilisateur/<id>/` | `profile_user` | Oui | GET/POST |
| `/profil/<id>/delete_review/` | `delete_review` | Oui | POST |
| `/profil/public/` | `profile_public` | Oui | GET (HTMX) |
| `/profil/info/` | `profile_info` | Oui | GET (HTMX) |
| `/profil/securité&connexion/` | `profile_security` | Oui | GET |
| `/profil/securité&connexion/password/` | `CustomPasswordChangeView` | Oui | GET/POST (CBV) |
| `/profil/securité&connexion/deactivate/` | `deactivate_account` | Oui | POST |
| `/email/display/` | `email_display` | Oui | GET |
| `/email/edit/` | `email_edit` | Oui | POST |
| `/email/change/confirm/<key>/` | `email_change_confirm` | Oui | GET |
| `/logout/` | `logout_user` | Oui | GET |

### Formulaires
| Formulaire | Type | Champs / validations notables |
|---|---|---|
| `CustomSignupForm` | SignupForm (allauth) | `service` obligatoire, `terms_accepted` obligatoire, `first_name`, `last_name`, `profile_picture`, `address` |
| `ProfileUpdateForm` | ModelForm | Photo profil, adresse, bio, langues, modes de transport, document BVM |
| `UserUpdateForm` | ModelForm | `first_name`, `last_name`, email (disabled) |
| `ChildForm` | ModelForm | Données enfant + langues |
| `ReviewForm` | ModelForm | Rating 1-5 + commentaire |
| `FavoriteAddressForm` | ModelForm | Label unique/user, adresse, coordonnées PostGIS |
| `TailwindFormMixin` | Mixin | Applique classes Tailwind par type widget |

### Signals
| Signal | Handler | Déclencheur | Effet |
|---|---|---|---|
| `email_confirmed` (allauth) | `email_confirmed_handler` | Confirmation d'un email secondaire | Supprime l'ancien email principal, promeut le nouveau, met à jour `user.email` |

### Logique métier
- **Onboarding multi-étapes** : `get_onboarding_steps()` retourne des étapes conditionnelles (nom, abonnement, CI, BVM, photo, enfant).
- `update_profile_verified()` : recalcule `prfl_is_verified` selon photo + adresse + langues.
- `trips_count` : property calculant le nombre de trajets confirmés passés.

### Intégrations externes
- **django-allauth** : email login, Google OAuth, MFA (TOTP, WebAuthn, recovery codes).
- **Stripe Identity** : vérification CI, stocke `verified_first_name` / `verified_last_name`.

---

## 3. App `trajects` — Moteur de Matching & Trajets

### Rôle métier
Cœur fonctionnel de la plateforme : création de trajets proposés/recherchés, moteur de matching géospatial, gestion des réservations.

### Modèles
| Modèle | Champs clés | Relations |
|---|---|---|
| `Traject` | `start_adress`, `end_adress`, `start_place_id`, `end_place_id`, `start_point` (PostGIS), `end_point` (PostGIS), `distance`, `created_at` | – |
| `TransportMode` | `name` (car/bike/transport/walking), `description` | M2M ← ProposedTraject, ResearchedTraject |
| `ProposedTraject` | `user` (FK), `traject` (FK), `groupe_name`, `groupe_uid` (UUID), `departure_time`, `arrival_time`, `number_of_places`, `search_radius_km` (défaut 5), `details`, `recurrence_type`, `recurrence_days`, `date`, `date_debut`, `date_fin`, `is_simple`, `is_active` | FK → User, FK → Traject, M2M → TransportMode, M2M → Languages, M2M → User (confirmed_users) |
| `ResearchedTraject` | `user` (FK), `traject` (FK), `groupe_uid` (UUID), `departure_time`, `arrival_time`, `recurrence_type`, `recurrence_days`, `date`, `date_debut`, `date_fin`, `is_active` | FK → User, FK → Traject, M2M → Child, M2M → TransportMode |
| `Reservation` | `user` (FK), `proposed_traject` (FK), `researched_traject` (FK), `number_of_places`, `status` (pending/confirmed/canceled), `reservation_date` | FK → User, FK → ProposedTraject, FK → ResearchedTraject, M2M → TransportMode |

### Vues (FBV, toutes `@login_required` sauf `autocomplete_view`)

**Propositions Yaya/Parent (trajet fixe) :**
| URL | Fonction | Méthode |
|---|---|---|
| `/trajets/propositions/nouveaux-trajets/` | `proposed_traject` | GET/POST |
| `/trajets/propositions/mes-trajets/` | `my_proposed_trajects` | GET |
| `/trajets/propositions/mes-trajets/<uuid>/` | `my_proposed_groupe_detail` | GET |
| `/trajets/propositions/delete/<uuid>/` | `delete_proposed_groupe` | POST |
| `/trajets/propositions/<uuid>/delete/<id>` | `delete_proposed_traject` | POST |
| `/trajets/propositions/matchings/` | `my_matchings_proposed` | GET |
| `/trajets/propositions/matchings/<uuid>/<uuid>/<id>/` | `my_matchings_proposed_detail` | GET/POST |

**Propositions Yaya rayon (sans destination) :**
| URL | Fonction | Méthode |
|---|---|---|
| `/trajets/recherches-rayon/nouvelles-recherches/` | `simple_proposed_traject` | GET/POST |
| `/trajets/recherches-rayon/mes-recherches/` | `my_simple_trajects` | GET |
| `/trajets/recherches-rayon/mes-recherches/<uuid>/` | `my_simple_groupe_detail` | GET |
| `/trajets/recherches-rayon/matchings/` | `my_matchings_simple` | GET |
| `/trajets/recherches-rayon/matchings/<uuid>/<uuid>/<id>/` | `my_matchings_simple_detail` | GET/POST |

**Recherches Parent :**
| URL | Fonction | Méthode |
|---|---|---|
| `/trajets/recherches/nouvelles-recherches/` | `researched_traject` | GET/POST |
| `/trajets/recherches/mes-recherches/` | `my_researched_trajects` | GET |
| `/trajets/recherches/mes-recherches/<uuid>/` | `my_researched_groupe_detail` | GET |
| `/trajets/recherches/matchings/` | `my_matchings_researched` | GET |
| `/trajets/recherches/matchings/<uuid>/<uuid>/<id>/` | `my_matchings_researched_detail` | GET/POST |

**Réservations :**
| URL | Fonction | Méthode |
|---|---|---|
| `/trajets/réservations/` | `my_reservations` | GET |
| `/trajets/réservations/reçue/<uuid>/` | `my_reservations_received_detail` | GET |
| `/trajets/manage_reservation/<id>/<action>/` | `manage_reservation` | POST |
| `/trajets/reservation/auto/<id>/<id>/` | `auto_reserve` | POST |
| `/trajets/propose-help/<id>/` | `propose_help` | POST |

**Utilitaires :**
| URL | Fonction | Méthode |
|---|---|---|
| `/trajets/autocomplete/` | `autocomplete_view` | GET (AJAX) |
| `/trajets/place-details/` | `place_details_view` | GET (AJAX) |

### Moteur de matching (fonctions privées)
| Fonction | Rôle |
|---|---|
| `find_matching_trajects(obj)` | Point d'entrée, dispatche selon le type |
| `find_matches_for_parent_research(research)` | Cherche des `ProposedTraject` dans un rayon PostGIS de 50 km, filtre Python (rayon, mode transport, créneau ±45 min, places) |
| `find_matches_for_precise_offer(proposal)` | Cherche des `ResearchedTraject` pour une offre fixe |
| `find_matches_for_simple_offer(simple_proposal)` | Cherche des `ResearchedTraject` dans un rayon (point départ uniquement) |
| `_time_ok(t1, t2, tolerance=45)` | Vérifie l'écart de temps entre deux horaires |
| `_same_transport_mode(...)` | Vérifie l'intersection des modes de transport |
| `_has_enough_places(proposal, researched)` | Vérifie les places disponibles vs. nombre d'enfants |

### Récurrence
- 3 types : `one_week` (occasionnel), `weekly` (hebdomadaire), `biweekly` (une semaine sur deux).
- `generate_recurrent_proposals()` / `generate_recurrent_researches()` : génèrent des instances individuelles avec `dateutil.rrule`.
- `disable_past_trajects` (management command) : désactive les trajets passés.

### Formulaires
| Formulaire | Modèle | Validations |
|---|---|---|
| `ProposedTrajectForm` | ProposedTraject | `RecurrenceValidationMixin` |
| `SimpleProposedTrajectForm` | ProposedTraject (is_simple=True) | `RecurrenceValidationMixin` |
| `ResearchedTrajectForm` | ResearchedTraject | `RecurrenceValidationMixin` |
| `ReservationForm` | Reservation | – |

### Décorateurs d'accès personnalisés
- `@name_required` : vérifie `first_name` + `last_name` remplis.
- `@subscription_complete_required` : vérifie abonnement actif.

---

## 4. App `chat` — Messagerie Temps Réel

### Rôle métier
Messagerie instantanée via WebSocket (Django Channels + Daphne). App en état **minimal/prototype** actuellement.

### Modèles
Aucun modèle défini (fichier `models.py` vide).

### Vues
| URL | Fonction | Auth | Description |
|---|---|---|---|
| `/chat/chat/` | `index` | Non | Rendu du template de chat (pas de `@login_required`) |

### Configuration Channels
- `ASGI_APPLICATION = 'bana.asgi:application'`
- `channels_redis` comme backend de channel layer.
- Daphne comme serveur ASGI (port 8001 en production).

### Points d'attention
- **Aucune persistence des messages** : pas de modèle `Message`.
- **Pas d'authentification** sur la vue chat.
- Le consumer WebSocket n'est pas présent dans le code Python analysé (pas de fichier `consumers.py` listé).

---

## 5. App `stripe_sub` — Paiements & Vérification Identité

### Rôle métier
Gestion des abonnements Stripe (checkout, webhooks) et vérification d'identité via Stripe Identity.

### Modèles
| Modèle | Champs clés | Relations |
|---|---|---|
| `Subscription` | `user` (FK), `stripe_customer_id`, `stripe_subscription_id`, `product_name`, `is_active`, `first_name`, `last_name`, `price`, `current_period_start`, `current_period_end`, `created_at` | FK → User |

### Vues
| URL | Fonction | Auth | Description |
|---|---|---|---|
| `/profil/abonnement/` | `subscription` | Oui | Affiche plan Stripe selon service (Parent/Yaya) |
| `/profil/checkout/` | `create_checkout_session` | Oui | Crée session Stripe Checkout |
| `/profil/abonnement/réussie/` | `payment_successful` | Oui | Page succès + sauvegarde abonnement |
| `/profil/abonnement/annulé/` | `payment_cancelled` | Non | Page annulation |
| `/profil/identité/` | `create_verification_session` | Oui | Lance Stripe Identity |
| `/profil/identité/complete/` | `identity_complete` | Oui | Page retour après vérification |
| `/webhook/stripe/` | `stripe_webhook` | Non (CSRF exempt) | Webhook Stripe (hors i18n_patterns) |

### Webhook — Événements gérés
| Événement Stripe | Action |
|---|---|
| `identity.verification_session.verified` | Marque `ci_is_verified=True`, extrait prénom/nom du rapport |
| `identity.verification_session.requires_input` | `ci_is_verified=False` |
| `identity.verification_session.canceled` | `ci_is_verified=False` |
| `checkout.session.completed` | Sauvegarde/met à jour l'abonnement en DB |
| `customer.subscription.created/updated` | Sauvegarde/met à jour ou désactive selon status |
| `invoice.payment_succeeded` | Met à jour l'abonnement après renouvellement |
| `customer.subscription.deleted` | Désactive l'abonnement |

### Bug identifié
`_update_profile_customer_id()` et `invoice.payment_succeeded` utilisent `Profile.objects.get(stripe_customer_id=...)` — **le champ `stripe_customer_id` n'existe pas sur le modèle `Profile`**. Il se trouve sur `Subscription`. Cela provoque une `FieldError` en production pour ces événements.

---

## 6. App `bug_tracker` — Suivi des Bugs

### Rôle métier
Outil interne de signalement et suivi de bugs (équipe de développement uniquement).

### Modèles
| Modèle | Champs clés |
|---|---|
| `Component` | `name`, `description` |
| `Version` | `name`, `release_date`, `is_active` |
| `Environment` | `name`, `description` |
| `Bug` | `title`, `description`, `reproduction_steps`, `status` (7 états), `priority` (4 niveaux), `severity` (5 niveaux), `component` (FK), `affected_version` (FK), `fixed_version` (FK null), `assigned_to` (FK null), `reported_by` (FK), `environment` (FK), `operating_system`, `browser`, `device` |
| `BugAttachment` | `bug` (FK), `file`, `filename`, `uploaded_by` (FK), `uploaded_at` |
| `BugComment` | `bug` (FK), `author` (FK), `content`, `created_at`, `updated_at` |
| `BugHistory` | `bug` (FK), `user` (FK), `field_changed`, `old_value`, `new_value`, `timestamp` |

### Vues (toutes `@login_required`)
| URL | Fonction | HTMX | Description |
|---|---|---|---|
| `/bug_tracker/` | `bug_list` | Oui | Liste paginée (20/page) avec filtres |
| `/bug_tracker/dashboard/` | `bug_stats` | Oui | Statistiques par priorité/composant |
| `/bug_tracker/create/` | `bug_create` | Oui | Création bug avec historique |
| `/bug_tracker/<id>/` | `bug_detail` | Non | Détail + commentaires + pièces jointes |
| `/bug_tracker/<id>/edit/` | `bug_edit` | Oui | Édition avec suivi des changements |
| `/bug_tracker/<id>/status/` | `bug_status_update` | Oui | Mise à jour statut |
| `/bug_tracker/<id>/assign/` | `bug_assign` | Oui | Assignation utilisateur |
| `/bug_tracker/<id>/comment/` | `add_comment` | Oui | Ajout commentaire |
| `/bug_tracker/<id>/upload/` | `upload_attachment` | Oui | Upload pièce jointe |

### Configuration upload
- Types MIME autorisés : JPEG, PNG, GIF, PDF, TXT, CSV, ZIP, DOC, DOCX.
- Taille max par fichier : 5 MB (`MAX_ATTACHMENT_SIZE`).
- `FILE_UPLOAD_MAX_MEMORY_SIZE` : 10 MB.

---

## 7. App `bana_admin` — Administration Interne

### Rôle métier
Dashboard admin : statistiques de visites, validation des profils membres, traçabilité.

### Modèles
| Modèle | Champs clés |
|---|---|
| `InscriptionValidation` | `user` (O2O), `is_validated`, `validation_date`, `notes`, `created_at`, `updated_at` |
| `SiteVisit` | `ip_address` (anonymisée), `user` (FK null), `timestamp`, `device_type` (mobile/tablet/desktop/unknown) |

### Vues
| URL | Fonction | Auth | Description |
|---|---|---|---|
| `/bana_admin/admin_view` | `admin_view` | Superuser | Vue générale admin avec tous les profils |
| `/bana_admin/validate_members` | `validate_members` | Superuser | Liste profils à valider (BVM, PRFL) |
| `/bana_admin/admin-panel/verify-prfl/<id>/` | `verify_profile_prfl` | Superuser | POST : valide `prfl_is_verified` |
| `/bana_admin/admin-panel/verify-bvm/<id>/` | `verify_bvm_prfl` | Superuser | POST : valide `bvm_is_verified` |
| `/bana_admin/admin/site-stats/` | `site_stats_view` | Superuser | Stats visites avec filtres temporels |
| `/bana_admin/wxc` | `ValidationListView` | Superuser (CBV) | Liste `InscriptionValidation` |
| `/bana_admin/<id>/validate/` | `ValidateUserView` | Superuser (CBV) | Valide une demande |
| `/bana_admin/<id>/reject/` | `RejectUserView` | Superuser (CBV) | Rejette une demande |

### Middleware `SiteVisitMiddleware`
- S'exécute après chaque requête non-statique.
- **Filtre** : bots (liste de 25+ signatures), chemins `/static/`, `/media/`, `/__reload__/`.
- **Anonymise** les IPs (IPv4 → `.0`, IPv6 → `/48`) — conformité RGPD.
- **Détecte** le type d'appareil (mobile/tablet/desktop).
- **Throttle** : une écriture DB max par IP/user toutes les 5 minutes.

### Management Commands
| Commande | Fichier | Description |
|---|---|---|
| `optimize_images` | `bana_admin/management/commands/optimize_images.py` | Convertit des images en WebP et redimensionne (Pillow) |
| `reset_visits` | `bana_admin/management/commands/reset_visits.py` | Purge `SiteVisit` avec confirmation |
| `disable_past_trajects` | `trajects/management/commands/disable_past_trajects.py` | Désactive les trajets dont la date est passée |

### Contrôle d'accès
- `SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin)` : seul mécanisme d'élévation.
- Les FBV admin utilisent `if not request.user.is_superuser: raise PermissionDenied`.

---

## 8. Récapitulatif global

| App | Modèles | Vues | Formulaires | Signals | CMD |
|---|---|---|---|---|---|
| `bana` | 0 | 13 | 0 | 0 | 0 |
| `accounts` | 5 | 20 | 6 | 1 | 0 |
| `trajects` | 5 | ~35 | 4 | 0 | 1 |
| `chat` | 0 | 1 | 0 | 0 | 0 |
| `stripe_sub` | 1 | 7 | 0 | 0 | 0 |
| `bug_tracker` | 5 | 9 | 4 | 0 | 0 |
| `bana_admin` | 2 | 8 | 0 | 0 | 2 |
| **Total** | **18** | **~93** | **14** | **1** | **3** |
