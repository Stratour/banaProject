# DEVIS — Développement BanaCommunity
## DU-2026-0619-001

---

```
┌─────────────────────────────────────┬────────────────────────────────────────┐
│ PRESTATAIRE                         │ CLIENT                                 │
│                                     │                                        │
│ Digit-Up Agency                     │ BanaCommunity                          │
│ Rue de Marcinelle 12                │ Attn. Nyota Delecourt — Fondatrice     │
│ 6000 Charleroi — Belgique           │ Charleroi — Belgique                   │
│ BCE : 0XXX.XXX.XXX                  │                                        │
│ TVA : BE 0XXX.XXX.XXX               │                                        │
│ contact@digit-up.be                 │ nyota@bana.mobi                        │
│ www.digit-up.be                     │ www.bana.mobi                          │
└─────────────────────────────────────┴────────────────────────────────────────┘

Numéro de devis   : DU-2026-0619-001
Date d'émission   : 19/06/2026
Valable jusqu'au  : 19/08/2026 (60 jours)
Référence projet  : BanaCommunity — Développement complet v2
Chef de projet    : Raphaël Jonard
```

---

## Objet de la prestation

Suite à l'audit applicatif réalisé en juin 2026, Digit-Up Agency propose le développement des fonctionnalités manquantes de la plateforme BanaCommunity (bana.mobi), ainsi que la correction des anomalies techniques identifiées.

Le périmètre complet est défini dans le **Cahier des Charges BanaCommunity v1.0** du 19/06/2026, document contractuel joint au présent devis.

---

## Conditions tarifaires

| Poste | Taux |
|---|---|
| Développement (senior) | **700,00 € HT / jour** |
| Développement (junior) | **450,00 € HT / jour** |
| Gestion de projet | **600,00 € HT / jour** |
| Recette & déploiement | **600,00 € HT / jour** |
| **TVA** | **21 %** (Belgique) |

*Un jour de prestation = 8 heures. Les estimations incluent : développement, tests unitaires, revue de code et documentation technique associée.*

---

## Détail des prestations

---

### PHASE 0 — Corrections critiques et dette technique
*Priorité absolue — prérequis à toutes les autres phases*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| COR-01 | Correction bug `stripe_customer_id` — ajout champ Profile, migration, tests webhook Stripe | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| COR-02 | Ajout `@login_required` sur vue chat | XS | 0,5 | 0,1 | 0,6 | 420,00 € |
| COR-03 | Configuration CORS — `CORS_ALLOWED_ORIGINS`, suppression doublon `cors-middleware` | XS | 0,5 | 0,1 | 0,6 | 420,00 € |
| COR-04 | Activation bannière cookies — intégration dans les deux layouts | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| COR-05 | Lien CGU dans footer et page inscription | XS | 0,5 | 0,1 | 0,6 | 420,00 € |
| COR-06 | Migration cache `LocMemCache` → Redis | S | 1,5 | 0,2 | 1,7 | 1 190,00 € |
| COR-07 | Migration Django 5.1.4 → 5.2 LTS + correction deprecation warnings + tests régression | M | 4,0 | 0,5 | 4,5 | 3 150,00 € |
| COR-08 | Personnalisation URL admin Django | XS | 0,5 | 0,1 | 0,6 | 420,00 € |
| — | **Recette & déploiement Phase 0** | — | — | 1,0 | 1,0 | 600,00 € |

**Sous-total Phase 0**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 11,5 j × 700 € | 8 050,00 € |
| Gestion de projet | 1,7 j × 600 € | 1 020,00 € |
| Recette & déploiement | 1,0 j × 600 € | 600,00 € |
| **Total Phase 0** | **14,2 jours** | **9 670,00 € HT** |

---

### PHASE 1 — Messagerie temps réel
*Fonctionnalité critique — prérequis à la confiance Parent/Yaya*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| MSG-01 | Modèles `Conversation`, `Message`, `MessageReadStatus` + migrations | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| MSG-02 | Consumer WebSocket authentifié (`ChatConsumer`) + routing ASGI + gestion déconnexion | M | 5,0 | 0,5 | 5,5 | 3 800,00 € |
| MSG-03 | Vues et URLs (liste conversations, détail, démarrer, mark-read, unread-count) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| MSG-04 | Templates UI messagerie (liste + bulles conversation) + JS WebSocket client | M | 5,0 | 0,5 | 5,5 | 3 800,00 € |
| MSG-05 | Badge messages non lus dans le header (HTMX polling + mise à jour WS) | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| MSG-06 | Boutons "Contacter" sur profil public et pages de matching | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| — | **Recette & déploiement Phase 1** | — | — | 2,0 | 2,0 | 1 200,00 € |

**Sous-total Phase 1**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 18,5 j × 700 € | 12 950,00 € |
| Gestion de projet | 2,0 j × 600 € | 1 200,00 € |
| Recette & déploiement | 2,0 j × 600 € | 1 200,00 € |
| **Total Phase 1** | **22,5 jours** | **15 350,00 € HT** |

---

### PHASE 2 — Système de notifications
*Requise pour activer la Formule Essentiel complète*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| NOTIF-01 | Module emails transactionnels : 7 emails (nouvelle réservation, confirmation, annulation, matching, rappel J-1, abonnement actif, expiration) + templates HTML | M | 5,0 | 0,5 | 5,5 | 3 800,00 € |
| NOTIF-02 | Push notifications Web : clés VAPID, modèle `PushSubscription`, API subscription JS, envoi push via `pywebpush` | L | 8,0 | 0,8 | 8,8 | 6 080,00 € |
| NOTIF-03 | Page préférences de notifications (email/push par catégorie) dans le profil | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| — | **Recette & déploiement Phase 2** | — | — | 1,5 | 1,5 | 900,00 € |

**Sous-total Phase 2**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 15,0 j × 700 € | 10 500,00 € |
| Gestion de projet | 1,6 j × 600 € | 960,00 € |
| Recette & déploiement | 1,5 j × 600 € | 900,00 € |
| **Total Phase 2** | **18,1 jours** | **12 360,00 € HT** |

---

### PHASE 3 — Calendrier et Planification
*Fonctionnalité centrale de la Formule Confort (149 €/an)*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| CAL-01 | Modèle `YayaUnavailability` + migration + impact sur le moteur de matching | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| CAL-02 | Vue calendrier mensuel/hebdomadaire + endpoint JSON events + intégration FullCalendar.js | L | 8,0 | 0,8 | 8,8 | 6 080,00 € |
| CAL-03 | CRUD indisponibilités Yaya (ajout, liste, suppression) | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| CAL-04 | Management command `send_trip_reminders` + configuration cron production | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| CAL-05 | Calendrier familial partagé (dépend Phase 7 — MULTI-01) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| — | **Recette & déploiement Phase 3** | — | — | 2,0 | 2,0 | 1 200,00 € |

**Sous-total Phase 3**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 19,5 j × 700 € | 13 650,00 € |
| Gestion de projet | 2,0 j × 600 € | 1 200,00 € |
| Recette & déploiement | 2,0 j × 600 € | 1 200,00 € |
| **Total Phase 3** | **23,5 jours** | **16 050,00 € HT** |

---

### PHASE 4 — Défraiement et Paiements Inter-Utilisateurs
*Requise pour la viabilité économique du modèle Yaya*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| DEF-01 | Modèles `DefraiementRate` et `TripPayment` + migration + admin Django | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| DEF-02 | Calcul automatique du défraiement à la confirmation de réservation | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| DEF-03 | Historique des revenus Yaya (liste paginée + filtres mois/statut + export CSV) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| DEF-04 | Historique des dépenses Parent (liste paginée + filtres + export CSV) | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| DEF-05 | Flux de confirmation de versement manuel (Parent marque "versé" + notif Yaya) | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| DEF-06 | Génération reçus PDF mensuels Yaya (WeasyPrint) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| — | **Recette & déploiement Phase 4** | — | — | 2,0 | 2,0 | 1 200,00 € |

**Sous-total Phase 4**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 18,5 j × 700 € | 12 950,00 € |
| Gestion de projet | 2,0 j × 600 € | 1 200,00 € |
| Recette & déploiement | 2,0 j × 600 € | 1 200,00 € |
| **Total Phase 4** | **22,5 jours** | **15 350,00 € HT** |

---

### PHASE 5 — Sécurité et Confiance
*Cœur de la valeur produit Bana*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| SEC-01 | Confirmation prise en charge : bouton Yaya + notification Parent + horodatage | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| SEC-02 | Confirmation arrivée enfant : bouton Yaya + notification Parent | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| SEC-03 | Signalement utilisateur : modèle `UserReport`, formulaire, interface admin bana_admin | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| SEC-04 | Blocage utilisateur : modèle `UserBlock`, action depuis profil, impact matching + chat | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| SEC-05 | Restriction des avis aux trajets effectués ensemble | S | 1,5 | 0,2 | 1,7 | 1 170,00 € |
| SEC-06 | Modération des avis : champs `is_published`, `is_flagged`, interface admin | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| — | **Recette & déploiement Phase 5** | — | — | 1,5 | 1,5 | 900,00 € |

**Sous-total Phase 5**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 16,0 j × 700 € | 11 200,00 € |
| Gestion de projet | 1,8 j × 600 € | 1 080,00 € |
| Recette & déploiement | 1,5 j × 600 € | 900,00 € |
| **Total Phase 5** | **19,3 jours** | **13 180,00 € HT** |

---

### PHASE 6 — RGPD et Conformité légale
*Obligation légale — conformité APD Belgique*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| RGPD-01 | Bannière cookie granulaire (3 catégories, stockage consentement, impact `SiteVisitMiddleware`) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| RGPD-02 | Intégration page Politique de Confidentialité *(contenu juridique à fournir par le client)* | S | 1,0 | 0,2 | 1,2 | 820,00 € |
| RGPD-03 | Export données personnelles : génération JSON/ZIP, vue profil, gestion asynchrone | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| RGPD-04 | Suppression complète du compte : délai 30 jours, email confirmation, anonymisation en cascade | L | 7,0 | 0,7 | 7,7 | 5 320,00 € |
| — | **Recette & déploiement Phase 6** | — | — | 1,5 | 1,5 | 900,00 € |

**Sous-total Phase 6**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 16,0 j × 700 € | 11 200,00 € |
| Gestion de projet | 1,7 j × 600 € | 1 020,00 € |
| Recette & déploiement | 1,5 j × 600 € | 900,00 € |
| **Total Phase 6** | **19,2 jours** | **13 120,00 € HT** |

---

### PHASE 7 — Expérience avancée et Administration
*Activation des Formules Confort/Premium et outils de pilotage*

| Réf. | Prestation | Complexité | Jours dev | Jours GP | Total jours | Prix HT |
|---|---|---|---|---|---|---|
| YAY-01 | Tableau de bord Yaya (KPIs mois, prochains trajets, réservations en attente) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| YAY-03 | Profil Yaya enrichi (zones de couverture, disponibilités, badges vérification) | S | 2,0 | 0,3 | 2,3 | 1 610,00 € |
| YAY-04 | Évaluation post-trajet automatique (trigger 24h après, email/push, formulaire) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| MAP-01 | Vue carte des matchings (Leaflet.js + OSM + clustering + endpoint GeoJSON) | L | 8,0 | 0,8 | 8,8 | 6 080,00 € |
| MAP-02 | Filtres avancés matching (distance, horaire, note min — HTMX) | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| MAP-03 | Notifications automatiques nouveaux matchings (management command + cron) | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| ADM-01 | Dashboard business admin (KPIs Stripe, taux conversion, trajets, utilisateurs actifs) | M | 5,0 | 0,5 | 5,5 | 3 800,00 € |
| ADM-02 | Export CSV/Excel : membres, réservations, abonnements | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| ADM-04 | Workflow validation BVM : file d'attente, visualisation doc, commentaire refus, log audit | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| ADM-05 | Outil emailing groupé admin (segmentation, éditeur, aperçu, envoi) | M | 4,0 | 0,4 | 4,4 | 3 040,00 € |
| MULTI-01 | Groupe famille : modèle `FamilyGroup`, invitations, acceptation, gestion membres | L | 5,0 | 0,5 | 5,5 | 3 800,00 € |
| MULTI-02 | Partage des enfants entre membres du groupe famille + impact trajets | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| CAL-05 | Calendrier familial partagé (agrégation événements groupe famille) | M | 3,0 | 0,3 | 3,3 | 2 280,00 € |
| — | **Recette & déploiement Phase 7** | — | — | 3,0 | 3,0 | 1 800,00 € |

**Sous-total Phase 7**

| | Jours | Montant HT |
|---|---|---|
| Développement senior | 50,0 j × 700 € | 35 000,00 € |
| Gestion de projet | 5,1 j × 600 € | 3 060,00 € |
| Recette & déploiement | 3,0 j × 600 € | 1 800,00 € |
| **Total Phase 7** | **58,1 jours** | **39 860,00 € HT** |

---

## Récapitulatif général

| Phase | Périmètre | Jours estimés | Montant HT |
|---|---|---|---|
| Phase 0 | Corrections critiques et dette technique | 14,2 j | 9 670,00 € |
| Phase 1 | Messagerie temps réel | 22,5 j | 15 350,00 € |
| Phase 2 | Système de notifications | 18,1 j | 12 360,00 € |
| Phase 3 | Calendrier et planification | 23,5 j | 16 050,00 € |
| Phase 4 | Défraiement et paiements | 22,5 j | 15 350,00 € |
| Phase 5 | Sécurité et confiance | 19,3 j | 13 180,00 € |
| Phase 6 | RGPD et conformité | 19,2 j | 13 120,00 € |
| Phase 7 | Expérience avancée et administration | 58,1 j | 39 860,00 € |
| | | | |
| **Sous-total développement** | | **197,4 j** | **134 940,00 €** |

---

### Réserve de contingence

Une réserve de **10 %** est appliquée pour couvrir les aléas techniques, les ajustements de spécifications en cours de développement et les intégrations imprévues avec des services tiers (Stripe, WebSocket, PostGIS).

| | Montant HT |
|---|---|
| Sous-total développement | 134 940,00 € |
| Réserve de contingence (10 %) | 13 494,00 € |
| **Total avant TVA** | **148 434,00 € HT** |

---

## Récapitulatif financier

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Total développement (197,4 jours)        134 940,00 € HT     │
│   Réserve de contingence (10 %)             13 494,00 € HT     │
│                                           ─────────────────     │
│   TOTAL HT                                148 434,00 € HT      │
│   TVA 21 %                                 31 171,14 €         │
│                                           ─────────────────     │
│   TOTAL TTC                               179 605,14 € TTC     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Options et variantes

### Option A — Périmètre prioritaire (Phases 0 + 1 + 2 + 6)
*Corriger les bugs critiques + messagerie + notifications + RGPD*

| Phase | Montant HT |
|---|---|
| Phase 0 — Corrections critiques | 9 670,00 € |
| Phase 1 — Messagerie | 15 350,00 € |
| Phase 2 — Notifications | 12 360,00 € |
| Phase 6 — RGPD | 13 120,00 € |
| Contingence 10 % | 5 050,00 € |
| **Total Option A HT** | **55 550,00 € HT** |
| TVA 21 % | 11 665,50 € |
| **Total Option A TTC** | **67 215,50 € TTC** |

*Durée estimée : 10-14 semaines*

---

### Option B — Périmètre commercial (Phases 0 à 4)
*Activer la Formule Confort : messagerie + notifications + calendrier + défraiement*

| Phase | Montant HT |
|---|---|
| Phase 0 — Corrections critiques | 9 670,00 € |
| Phase 1 — Messagerie | 15 350,00 € |
| Phase 2 — Notifications | 12 360,00 € |
| Phase 3 — Calendrier | 16 050,00 € |
| Phase 4 — Défraiement | 15 350,00 € |
| Contingence 10 % | 6 878,00 € |
| **Total Option B HT** | **75 658,00 € HT** |
| TVA 21 % | 15 888,18 € |
| **Total Option B TTC** | **91 546,18 € TTC** |

*Durée estimée : 24-30 semaines*

---

### Option C — Périmètre complet (Phases 0 à 7)
*Plateforme complète prête pour Formules Essentiel, Confort et Premium*

| | Montant HT |
|---|---|
| **Total Option C HT** | **148 434,00 € HT** |
| TVA 21 % | 31 171,14 € |
| **Total Option C TTC** | **179 605,14 € TTC** |

*Durée estimée : 40-53 semaines*

---

## Modalités de paiement

### Phasage de facturation

La facturation est réalisée **par phase livrée et recettée** selon le calendrier suivant :

| Facturation | Montant | Condition |
|---|---|---|
| Acompte démarrage | 30 % du total phase | À la signature du bon de commande |
| Mi-phase | 40 % du total phase | À mi-parcours (point d'avancement validé) |
| Solde phase | 30 % du total phase | À la livraison et recette validée |

### Conditions générales de paiement

- **Délai de paiement :** 30 jours date de facture
- **Mode de paiement :** virement bancaire (IBAN communiqué sur facture)
- **Pénalités de retard :** taux légal belge en vigueur + indemnité forfaitaire de recouvrement de 40 €
- **Bon de commande :** un bon de commande signé est requis avant tout démarrage de phase

---

## Conditions d'exécution

### Responsabilités du prestataire (Digit-Up Agency)

- Développement conforme au Cahier des Charges v1.0 du 19/06/2026
- Livraison du code source versionné (Git) à chaque fin de phase
- Rédaction des migrations Django et documentation technique associée
- Tests unitaires sur les nouvelles fonctionnalités
- Support pendant la recette : 10 jours ouvrables après chaque livraison
- Déploiement en production ou assistance au déploiement

### Responsabilités du client (BanaCommunity)

- Fourniture des accès nécessaires (serveur, Git, Stripe, services tiers) dans les 5 jours ouvrables suivant la signature
- Fourniture du contenu textuel requis (politique de confidentialité, textes légaux)
- Désignation d'un interlocuteur unique côté client pour les validations fonctionnelles
- Validation ou retours sur livraisons dans un délai de **10 jours ouvrables**
- Toute demande de modification hors périmètre CDC fera l'objet d'un avenant

### Gestion des modifications de périmètre

Toute demande de modification du périmètre défini dans le CDC fera l'objet :
1. D'une analyse d'impact (gratuite, ≤ 2h)
2. D'un avenant chiffré soumis à validation
3. D'un ajustement du planning si nécessaire

### Propriété intellectuelle

À la livraison complète et au règlement intégral de chaque phase, BanaCommunity devient propriétaire du code source développé dans le cadre du présent devis. Les bibliothèques open source utilisées (Django, Tailwind, Leaflet, FullCalendar, etc.) restent soumises à leurs licences respectives.

### Confidentialité

Digit-Up Agency s'engage à maintenir la confidentialité de toutes les informations relatives au projet BanaCommunity. Un accord de confidentialité (NDA) peut être signé à la demande du client.

---

## Planning indicatif (périmètre complet)

```
2026
Juil.  ████████ Phase 0 — Corrections critiques (3 sem.)
Août   ████████████████████████ Phase 1 — Messagerie (8 sem.)
Sept.  ████████
Oct.   ████████████████ Phase 2 — Notifications (6 sem.)
Nov.   ████████
       ████████████████████████ Phase 3 — Calendrier (8 sem.)
Déc.   ████████
2027
Jan.   ████████████████ Phase 4 — Défraiement (8 sem.)
Fév.   ████████
Mar.   ████████████ Phase 5 — Sécurité (5 sem.)
Avr.   █████████████████████████████ Phase 6 — RGPD (5 sem.)
Mai    ████████████████████████████████████████ Phase 7 (10 sem.)
Juin   ████████████████████████████████████████
Juil.  ████████████████████████████████████████
Août   ████████████████
```

*Planning conditionné à la signature et au démarrage avant le 01/08/2026. Décalages possibles selon disponibilités des ressources et retours client.*

---

## Validité et acceptation

Le présent devis est valable **60 jours** à compter de sa date d'émission, soit jusqu'au **19/08/2026**.

Pour acceptation, merci de retourner ce document signé accompagné d'un bon de commande à :
**contact@digit-up.be**

```
Lu et approuvé — Bon pour accord

Fait à __________________, le __________________

Pour BanaCommunity :                    Pour Digit-Up Agency :

Nom : ______________________            Nom : Raphaël Jonard
Fonction : _________________            Fonction : Directeur Technique
Signature :                             Signature :


____________________________            ____________________________
```

---

*Digit-Up Agency — Rue de Marcinelle 12 — 6000 Charleroi — Belgique*
*BCE : 0XXX.XXX.XXX — TVA : BE 0XXX.XXX.XXX — IBAN : BEXX XXXX XXXX XXXX*
*contact@digit-up.be — www.digit-up.be*
