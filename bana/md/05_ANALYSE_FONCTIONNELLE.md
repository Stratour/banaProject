# 05 — Analyse Fonctionnelle — Existant vs Manquant
**Objectif :** Base de travail pour la rédaction d'un cahier des charges complet en vue d'un devis
**Projet :** BanaCommunity (bana.mobi)
**Analyste :** Digit-Up Agency
**Date :** 2026-06-19

---

## Méthode de lecture

Chaque fonctionnalité est classée selon son état réel :
- ✅ **Implémentée** — fonctionnelle et déployée
- 🟡 **Partielle** — code présent mais incomplète ou buguée
- 🔴 **Absente** — mentionnée dans les offres tarifaires ou logiquement attendue, non implémentée
- 📌 **Hors scope actuel** — fonctionnalité future à concevoir

---

## PARTIE 1 — Fonctionnalités existantes (état réel)

### 1.1 Inscription & Authentification

| Fonctionnalité | État | Détail |
|---|---|---|
| Inscription par email | ✅ | Email-only via allauth, formulaire custom avec `service` (Parent/Yaya) |
| Vérification email obligatoire | ✅ | `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` |
| Connexion par email | ✅ | allauth |
| Connexion Google OAuth | ✅ | `allauth.socialaccount.providers.google` configuré |
| Réinitialisation mot de passe | ✅ | allauth standard |
| Changement d'email | ✅ | Flux custom avec email de confirmation + signal promotion |
| Désactivation de compte | ✅ | `user.is_active = False` + déconnexion |
| 2FA TOTP | ✅ | allauth MFA — TOTP configuré |
| Passkeys (WebAuthn) | ✅ | allauth MFA — WebAuthn configuré |
| Codes de récupération | ✅ | allauth MFA |
| Anti-énumération emails | ✅ | `ACCOUNT_PREVENT_ENUMERATION = True` |
| Acceptation CGU à l'inscription | ✅ | Champ `terms_accepted` obligatoire |
| Gestion sessions actives | ✅ | `usersessions` allauth (template présent) |

---

### 1.2 Profil Utilisateur

| Fonctionnalité | État | Détail |
|---|---|---|
| Photo de profil | ✅ | Upload ImageField |
| Biographie | ✅ | TextField |
| Adresse (code postal / ville) | ✅ | CharField |
| Langues parlées | ✅ | ManyToMany Languages |
| Modes de transport préférés | ✅ | JSONField |
| Rôle (Parent / Yaya) | ✅ | Choisi à l'inscription, stocké dans `service` |
| Vérification identité (CI) | ✅ | Stripe Identity — `ci_is_verified`, `verified_first_name/last_name` |
| Dépôt casier judiciaire (BVM) | ✅ | Upload FileField, validation manuelle admin |
| Onboarding multi-étapes | 🟡 | Checklist visible, mais les étapes CI/BVM/photo ne bloquent pas l'accès aux trajets |
| Profil vérifié automatique | 🟡 | `update_profile_verified()` recalcule mais n'est appelé qu'à l'édition |
| Profil public consultable | ✅ | `/profil/utilisateur/<id>/` avec avis et étoiles |
| Compteur de trajets effectués | ✅ | Property `trips_count` (trajets confirmés passés) |
| Adresses favorites (GIS) | ✅ | `FavoriteAddress` avec PostGIS PointField, unique par label/user |

---

### 1.3 Gestion Enfants (Parent)

| Fonctionnalité | État | Détail |
|---|---|---|
| Ajout enfant | ✅ | Nom, prénom, date naissance, genre, siège, handicap, langues |
| Suppression enfant | ✅ | |
| Besoins spécifiques enfant | ✅ | TextField libre |
| Age calculé automatiquement | ✅ | Property `age` |
| Multi-enfants | ✅ | Plusieurs enfants par compte Parent |

---

### 1.4 Trajets — Création et Gestion

| Fonctionnalité | État | Détail |
|---|---|---|
| Proposition trajet fixe (Yaya/Parent) | ✅ | `ProposedTraject` avec départ, arrivée, horaires, places, modes transport |
| Proposition trajet rayon (Yaya) | ✅ | `ProposedTraject is_simple=True` — rayon uniquement, sans destination |
| Recherche trajet (Parent) | ✅ | `ResearchedTraject` avec enfants, horaires, modes transport |
| Autocomplete adresses | ✅ | OpenStreetMap + Google Maps API |
| Géocodage coordonnées | ✅ | `geopy`, stockage PostGIS |
| Récurrence — occasionnel | ✅ | `one_week` : jours sélectionnés sur une période |
| Récurrence — hebdomadaire | ✅ | `weekly` : mêmes jours chaque semaine |
| Récurrence — bimensuel | ✅ | `biweekly` : une semaine sur deux |
| Génération dates récurrentes | ✅ | `dateutil.rrule` |
| Désactivation trajets passés | ✅ | Management command `disable_past_trajects` |
| Groupes de trajets (uuid) | ✅ | `groupe_uid` — permet de lier des trajets récurrents |
| Suppression groupe / trajet individuel | ✅ | Vues delete avec `@transaction.atomic` |
| Détail groupe (dates, statuts) | ✅ | Template `trajet_detail.html` |

---

### 1.5 Moteur de Matching

| Fonctionnalité | État | Détail |
|---|---|---|
| Matching parent → Yaya (trajet fixe) | ✅ | PostGIS 50 km pré-filtre + filtre Python radius, transport, créneau ±45 min, places |
| Matching Yaya → parent (trajet fixe) | ✅ | `find_matches_for_precise_offer()` |
| Matching Yaya rayon → parent | ✅ | `find_matches_for_simple_offer()` — point départ uniquement |
| Filtre par mode de transport | ✅ | Intersection des modes |
| Filtre par créneau horaire | ✅ | Tolérance ±45 minutes |
| Filtre par places disponibles | ✅ | `_has_enough_places()` |
| Vue liste matchings | ✅ | `my_matchings_proposed`, `my_matchings_researched`, `my_matchings_simple` |
| Détail matching | ✅ | Avec profil utilisateur, dates matchées |
| Tri/affichage par groupe | ✅ | `_aggregate_groupes()` |

---

### 1.6 Réservations

| Fonctionnalité | État | Détail |
|---|---|---|
| Création réservation (parent) | ✅ | `auto_reserve()` et `propose_help()` |
| Gestion réservation (yaya) | ✅ | `manage_reservation()` — confirmer/annuler |
| Statuts réservation | ✅ | pending / confirmed / canceled |
| Liste réservations côté parent | ✅ | Groupées par `(proposed_groupe_uid, yaya)` |
| Liste réservations côté yaya | ✅ | Groupées par `proposed_groupe_uid` avec annotations ORM |
| Détail réservations reçues | ✅ | Par parent avec dates et places restantes |
| Décompte des places disponibles | ✅ | `_available_places()` — soustrait les réservations confirmées |

---

### 1.7 Paiements & Abonnements

| Fonctionnalité | État | Détail |
|---|---|---|
| Abonnement Yaya (2€/an) | ✅ | `yaya_annual_2e` lookup key Stripe |
| Abonnement Parent (99€/an) | ✅ | `parent_annual_99e` lookup key Stripe |
| Checkout Stripe | ✅ | Session Stripe Checkout |
| Page paiement réussi | 🟡 | Fonctionne mais le mapping `stripe_customer_id` sur Profile est cassé (BUG-01/02) |
| Renouvellement automatique | 🔴 | `invoice.payment_succeeded` échoue → abonnement non renouvelé en DB |
| Annulation abonnement | 🟡 | Webhook `customer.subscription.deleted` présent mais non testé |
| Vérification identité Stripe | 🟡 | Flow OK mais mapping customer cassé |
| Gestion multi-plans | 🔴 | Formules Confort/Premium visibles dans les tarifs mais non implémentées côté Stripe |

---

### 1.8 Messagerie

| Fonctionnalité | État | Détail |
|---|---|---|
| Interface chat | 🟡 | Template `chat/index.html` présent, route existante |
| WebSocket (Channels/Daphne) | 🟡 | Infrastructure configurée, pas de consumer implémenté |
| Modèle Message | 🔴 | Inexistant — aucune persistance |
| Conversations privées | 🔴 | Non implémenté |
| Notifications messages non lus | 🔴 | Non implémenté |

---

### 1.9 Avis & Notation

| Fonctionnalité | État | Détail |
|---|---|---|
| Déposer un avis | ✅ | Note 1-5 + commentaire |
| Modifier son avis | ✅ | Edit sur le même objet Review |
| Supprimer son avis | ✅ | |
| Moyenne étoiles affichée | ✅ | Calcul + affichage demi-étoile |
| Profil public avec avis | ✅ | `/profil/utilisateur/<id>/` |
| Modération des avis | 🔴 | Non implémentée |
| Limitation avis/trajet confirmé | 🔴 | Tout utilisateur connecté peut noter n'importe quel autre utilisateur |

---

### 1.10 Administration & Back-office

| Fonctionnalité | État | Détail |
|---|---|---|
| Admin Django standard | ✅ | `/admin/` — tous les modèles accessibles |
| Validation profils BVM | ✅ | Interface bana_admin avec bouton de validation |
| Validation profils PRFL | ✅ | |
| Statistiques de visites | ✅ | `site_stats_view` — visites par période, device type, KPIs |
| Filtre temporel (jour/semaine/mois/année) | ✅ | |
| Pagination visites | ✅ | |
| Gestion bugs (bug_tracker) | ✅ | Liste, détail, commentaires, pièces jointes, historique |
| Statistiques bugs | ✅ | Dashboard par priorité/composant |
| Commandes de maintenance | ✅ | `disable_past_trajects`, `reset_visits`, `optimize_images` |

---

### 1.11 PWA & SEO

| Fonctionnalité | État | Détail |
|---|---|---|
| Application installable (PWA) | ✅ | Manifest, service worker, icônes maskable |
| Page offline | ✅ | |
| Sitemap XML | ✅ | `StaticViewSitemap` |
| robots.txt | ✅ | Restrictif, autorise uniquement les pages publiques |
| i18n (fr/en/nl) | ✅ | `i18n_patterns`, sélecteur de langue |
| Traductions compilées | 🟡 | Structure i18n en place, complétude des traductions en/nl à vérifier |

---

### 1.12 Sécurité & RGPD

| Fonctionnalité | État | Détail |
|---|---|---|
| Anonymisation IP | ✅ | IPv4 → `/24`, IPv6 → `/48` dans `SiteVisitMiddleware` |
| Bannière cookies | 🟡 | Fichier CSS/JS/HTML présent mais non committé, non intégré |
| Conditions générales | 🟡 | PDF présent (`doc/conditions-generales-utilisation.pdf`) mais non lié depuis les templates |
| Suppression de compte | ✅ | `deactivate_account()` — désactive `is_active` |
| Suppression données utilisateur | 🔴 | Pas de procédure RGPD de suppression complète des données |
| Consentement cookies granulaire | 🔴 | Non implémenté |
| Export données personnelles | 🔴 | Non implémenté |

---

## PARTIE 2 — Fonctionnalités manquantes identifiées

Les fonctionnalités ci-dessous sont **absentes du code** mais attendues soit par le modèle économique (tarifaire), soit par les exigences métier ou réglementaires.

---

### 2.1 Messagerie Temps Réel (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Modèle `Message` (conversation, expéditeur, contenu, timestamp, lu/non lu) | Infrastructure chat présente, aucune persistance | Moyenne |
| Consumers WebSocket authentifiés | Django Channels configuré, pas de consumer | Moyenne |
| Conversations privées Parent ↔ Yaya | Nécessaire avant tout engagement de trajet | Haute |
| Notification de nouveau message (badge, push) | Expérience utilisateur critique | Haute |
| Historique des conversations | RGPD + sécurité des échanges | Moyenne |
| Partage de localisation dans le chat | Sécurité lors des prises en charge | Haute |

---

### 2.2 Notifications (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Email transactionnel — nouvelle réservation | Actuellement aucun email de réservation envoyé | Faible |
| Email transactionnel — réservation confirmée/annulée | Idem | Faible |
| Email transactionnel — nouveau matching | Mentionné dans Formule Essentiel | Faible |
| Notifications push Web (service worker) | PWA installée, aucune notification push | Haute |
| Rappels automatiques (veille trajet) | Mentionné dans Formule Confort | Haute |
| Notifications intelligentes | Mentionné dans Formule Confort | Haute |
| SMS (optionnel) | Sécurité lors des prises en charge | Haute |

---

### 2.3 Calendrier & Planification (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Calendrier personnel (vue hebdo/mensuelle) | Mentionné dans Formule Confort (149€/an) | Haute |
| Vue calendrier des trajets confirmés | Gestion planning famille | Haute |
| Calendrier familial partagé | Mentionné dans Formule Premium (199€/an) | Très haute |
| Rappels automatiques de trajets | Formule Confort | Haute |
| Synchronisation calendrier externe (Google Cal, iCal) | Attendu par les utilisateurs | Très haute |
| Gestion des indisponibilités Yaya | Permettre au Yaya de bloquer des dates | Moyenne |

---

### 2.4 Défraiement & Paiements Inter-Utilisateurs (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Modèle de défraiement par trajet | Barème affiché dans tarifs (3€-7€/trajet) mais non implémenté | Haute |
| Enregistrement des paiements Yaya | Suivi des défraiements versés | Haute |
| Historique des trajets défrayés | Formule Confort — "Historique des trajets" | Haute |
| Calcul automatique du défraiement | Selon distance/durée | Haute |
| Virement/paiement Stripe Connect | Pour sécuriser les paiements inter-utilisateurs | Très haute |
| Reçus/attestations fiscales | Pour les Yaya (revenus activité) | Haute |

---

### 2.5 Sécurité & Confiance (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Confirmation prise en charge (message envoi enfant) | Mentionné dans `work.html` comme feature | Haute |
| Confirmation arrivée enfant | Idem | Haute |
| Badge enfant personnalisé | Formule Premium | Haute |
| Partage de localisation temps réel pendant le trajet | Sécurité parents | Très haute |
| Assurance enfant incluse | Formule Premium — à sous-traiter (partenaire) | Très haute |
| Signalement/blocage utilisateur | Sécurité communauté | Moyenne |
| Modération des avis | Prévention abus | Moyenne |
| Restriction des avis aux trajets confirmés | Intégrité des notes | Faible |

---

### 2.6 Gestion Multi-Utilisateurs & Famille (Formule Premium)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Accès multi-utilisateurs (ex: deux parents) | Mentionné Formule Premium | Haute |
| Délégation de gestion (grand-parent, assistante) | Attendu dans un contexte famille | Haute |
| Partage de profil enfant entre membres famille | Formule Premium | Haute |

---

### 2.7 Expérience Yaya

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Tableau de bord Yaya (trajets acceptés, défraiement total) | Pas de vue synthétique Yaya | Moyenne |
| Déclaration d'indisponibilité | Permettre au Yaya de se rendre indisponible sur une période | Moyenne |
| Historique des trajets effectués avec revenus | Formule Confort | Haute |
| Évaluation des enfants / parents par le Yaya | Système de notation bidirectionnel | Moyenne |
| Profil Yaya avec portfolio (compétences, langues, zones) | Améliorer la confiance | Faible |

---

### 2.8 Recherche Avancée & Carte (priorité moyenne)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Vue carte (MapBox / Leaflet) des matchings | Intuitivité du matching géospatial | Haute |
| Filtres avancés (distance, horaire, étoiles min.) | Matching plus précis | Moyenne |
| Recommandations automatiques (matchings notifiés) | Formule Essentiel — "Notifications nouveaux matchings" | Haute |
| Recherche de profils sans trajet | Pour rentrer en contact avant de créer un trajet | Moyenne |

---

### 2.9 RGPD & Conformité (priorité haute)

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Bannière cookie avec granularité (analytics, marketing, fonctionnel) | RGPD obligatoire | Moyenne |
| Page de politique de confidentialité | RGPD + confiance | Faible |
| Export des données personnelles (JSON/PDF) | Droit à la portabilité RGPD | Moyenne |
| Suppression complète des données | Droit à l'effacement RGPD | Haute |
| Consentement explicite aux traitements | RGPD article 7 | Haute |
| Registre de traitements | Conformité interne RGPD | Faible |

---

### 2.10 Administration Avancée

| Fonctionnalité | Justification | Complexité |
|---|---|---|
| Dashboard admin avancé (revenus, transactions) | Vision business | Haute |
| Export CSV/Excel des données | Reporting direction | Moyenne |
| Gestion des remboursements Stripe | Back-office paiement | Haute |
| Tableau de bord matching (taux de succès) | Mesure efficacité produit | Haute |
| Workflow de validation BVM simplifié | Actuellement manuel | Moyenne |
| Outil de communication email groupé (newsletters) | Engagement membres | Haute |

---

### 2.11 Corrections Techniques (non fonctionnelles mais bloquantes)

| Fonctionnalité | Priorité | Complexité |
|---|---|---|
| Corriger bug `stripe_customer_id` sur Profile | 🔴 Critique | Faible |
| Implémenter consumer WebSocket chat | 🔴 Critique | Haute |
| Ajouter `@login_required` sur vue chat | 🔴 Critique | Très faible |
| Configurer CORS | 🔴 Critique | Très faible |
| Activer bannière cookie (CSS/JS déjà présents) | 🔴 Haute | Faible |
| Lier CGU dans les templates | 🟡 Modérée | Très faible |
| Migrer cache vers Redis | 🟡 Modérée | Faible |
| Migrer vers Django 5.2 LTS | 🟡 Modérée | Moyenne |

---

## PARTIE 3 — Estimation de Complétude par Module

| Module | % Complétude | État général |
|---|---|---|
| Inscription / Auth | 90% | Très complet — MFA, OAuth, allauth |
| Profil utilisateur | 75% | Bon — manque la suppression RGPD complète |
| Gestion enfants | 95% | Complet |
| Création trajets | 85% | Bon — quelques champs null à nettoyer |
| Moteur de matching | 80% | Fonctionnel — pas de vue carte |
| Réservations | 80% | Bon — pas de notifications |
| Messagerie | 10% | Infrastructure uniquement, rien de fonctionnel |
| Notifications | 5% | Quasi inexistant |
| Calendrier | 0% | Non implémenté |
| Défraiement | 5% | Affiché dans tarifs, non codé |
| Abonnements Stripe | 70% | Bug critique sur renouvellement |
| Vérification identité | 70% | Bug customer mapping |
| Avis & Notation | 70% | Pas de modération ni restriction |
| PWA | 80% | Notifications push manquantes |
| i18n | 65% | Structure présente, traductions incomplètes |
| RGPD | 30% | IP anonymisée, bannière cookie non active |
| Administration | 60% | Basic, pas d'export ni de reporting |
| Sécurité | 80% | Bon niveau — quelques corrections à apporter |

**Complétude globale estimée : ~60%**

---

## PARTIE 4 — Roadmap Recommandée (pour devis)

### Phase 1 — Corrections critiques (Sprint 1-2 — ~3 semaines)
- Corriger bug `stripe_customer_id` (BUG-01/02)
- Ajouter `@login_required` chat
- Configurer CORS
- Activer bannière cookies + lier CGU
- Migrer cache vers Redis
- Mise à jour Django 5.2 LTS

### Phase 2 — Messagerie & Notifications (Sprint 3-6 — ~8 semaines)
- Modèle `Message` + consumers WebSocket authentifiés
- Conversations privées Parent ↔ Yaya
- Emails transactionnels (réservations, matchings)
- Notifications push PWA (service worker)
- Badges messages non lus

### Phase 3 — Calendrier & Planification (Sprint 7-10 — ~8 semaines)
- Vue calendrier hebdomadaire/mensuelle
- Intégration Google Calendar (optionnel)
- Rappels automatiques (24h avant trajet)
- Gestion indisponibilités Yaya

### Phase 4 — Sécurité & Confiance (Sprint 11-14 — ~8 semaines)
- Confirmation prise en charge / arrivée enfant
- Partage de localisation temps réel
- Modération des avis + restriction aux trajets confirmés
- Signalement/blocage utilisateur
- Badge enfant personnalisé (Formule Premium)

### Phase 5 — Défraiement & Paiements (Sprint 15-18 — ~8 semaines)
- Modèle de défraiement par trajet
- Historique des paiements Yaya
- Intégration Stripe Connect
- Reçus fiscaux

### Phase 6 — RGPD & Conformité (Sprint 19-20 — ~4 semaines)
- Export données personnelles
- Suppression complète des données
- Politique de confidentialité
- Registre de traitements

### Phase 7 — Expérience avancée (Sprint 21-24 — ~8 semaines)
- Vue carte des matchings (Leaflet/Mapbox)
- Filtres avancés matching
- Tableau de bord Yaya
- Accès multi-utilisateurs (Formule Premium)
- Administration avancée (export, reporting)

---

## PARTIE 5 — Récapitulatif pour Devis

| Phase | Périmètre | Complexité estimée |
|---|---|---|
| P1 — Corrections critiques | 8 corrections | ~3 sem. / 1 dev |
| P2 — Messagerie & Notifications | 9 fonctionnalités | ~8 sem. / 1-2 devs |
| P3 — Calendrier | 5 fonctionnalités | ~8 sem. / 1 dev |
| P4 — Sécurité & Confiance | 8 fonctionnalités | ~8 sem. / 1-2 devs |
| P5 — Défraiement | 6 fonctionnalités | ~8 sem. / 1 dev |
| P6 — RGPD | 6 fonctionnalités | ~4 sem. / 1 dev |
| P7 — Expérience avancée | 8 fonctionnalités | ~8 sem. / 1-2 devs |
| **Total** | **~50 fonctionnalités** | **~47 sem.** |

> Ces estimations sont indicatives. Chaque phase doit faire l'objet d'une spécification détaillée avant chiffrage définitif.
