# Cahier des Charges — BanaCommunity
## Plateforme de mobilité partagée et d'accompagnement des enfants

---

| | |
|---|---|
| **Projet** | BanaCommunity — bana.mobi |
| **Commanditaire** | Nyota Delecourt — Fondatrice BanaCommunity |
| **Prestataire** | Digit-Up Agency — Charleroi, Belgique |
| **Contact technique** | Raphaël Jonard — Développeur principal |
| **Version** | 1.0 |
| **Date** | 2026-06-19 |
| **Statut** | Draft — à valider par le commanditaire |

---

## Table des matières

1. [Contexte et présentation du projet](#1-contexte-et-présentation-du-projet)
2. [Objectifs du projet](#2-objectifs-du-projet)
3. [Parties prenantes](#3-parties-prenantes)
4. [Périmètre du projet](#4-périmètre-du-projet)
5. [Architecture existante](#5-architecture-existante)
6. [Spécifications fonctionnelles — Existant à corriger](#6-spécifications-fonctionnelles--existant-à-corriger)
7. [Spécifications fonctionnelles — Nouvelles fonctionnalités](#7-spécifications-fonctionnelles--nouvelles-fonctionnalités)
   - 7.1 Messagerie temps réel
   - 7.2 Système de notifications
   - 7.3 Calendrier et planification
   - 7.4 Défraiement et paiements inter-utilisateurs
   - 7.5 Sécurité et confiance
   - 7.6 RGPD et conformité
   - 7.7 Expérience Yaya
   - 7.8 Recherche avancée et cartographie
   - 7.9 Administration avancée
   - 7.10 Gestion multi-utilisateurs (Formule Premium)
8. [Spécifications techniques](#8-spécifications-techniques)
9. [Contraintes et exigences transversales](#9-contraintes-et-exigences-transversales)
10. [Maquettes fonctionnelles (description)](#10-maquettes-fonctionnelles-description)
11. [Phasage et planning](#11-phasage-et-planning)
12. [Livrables](#12-livrables)
13. [Critères d'acceptation](#13-critères-dacceptation)
14. [Glossaire](#14-glossaire)

---

## 1. Contexte et présentation du projet

### 1.1 Présentation de BanaCommunity

BanaCommunity est une startup belge fondée à Charleroi, opérant via le domaine **bana.mobi**. La plateforme met en relation des **parents** ayant besoin d'accompagnement pour leurs enfants (trajets école, activités extrascolaires) avec des **Yaya** — adultes de confiance de la communauté prêts à effectuer ces trajets.

Le modèle repose sur trois piliers :
- **La confiance** : vérification d'identité (Carte d'identité via Stripe Identity), vérification du casier judiciaire (BVM extrait 596.2), validation manuelle par l'équipe Bana.
- **La communauté** : mise en relation de voisins partageant des trajets similaires.
- **L'accessibilité** : tous les modes de transport sont acceptés (voiture, vélo, transports en commun, marche à pied).

BanaCommunity est soutenue par Start it @KBC, Cap Innove, et des partenaires matériels (Materne, Alvityl). La plateforme a reçu 3 prix depuis sa création.

### 1.2 Situation actuelle

La plateforme existe en production (bana.mobi) avec un socle fonctionnel couvrant l'inscription, la vérification d'identité, la création et le matching de trajets, la gestion des réservations, et les abonnements Stripe.

Un audit technique conduit en juin 2026 par Digit-Up Agency a établi que **la plateforme est complète à environ 60%**. Des fonctionnalités annoncées dans les offres tarifaires (calendrier, notifications, défraiement, messagerie, Formule Confort/Premium) ne sont pas encore implémentées. Plusieurs bugs critiques affectent le renouvellement des abonnements.

### 1.3 Objectif du cahier des charges

Ce document constitue la **référence contractuelle** pour le développement des fonctionnalités manquantes et la correction des bugs existants. Il est destiné à servir de base à un devis détaillé et à un planning de développement.

---

## 2. Objectifs du projet

### 2.1 Objectifs fonctionnels

| # | Objectif | Priorité |
|---|---|---|
| OF-01 | Corriger les bugs critiques bloquant les paiements Stripe | 🔴 Critique |
| OF-02 | Implémenter la messagerie temps réel entre Parent et Yaya | 🔴 Critique |
| OF-03 | Mettre en place les notifications (email + push) | 🔴 Haute |
| OF-04 | Développer le module calendrier (Formule Confort) | 🔴 Haute |
| OF-05 | Implémenter le système de défraiement et l'historique financier | 🔴 Haute |
| OF-06 | Renforcer les mécanismes de sécurité et de confiance | 🟡 Haute |
| OF-07 | Assurer la conformité RGPD complète | 🔴 Haute (légale) |
| OF-08 | Développer les fonctionnalités Formule Premium | 🟡 Moyenne |
| OF-09 | Améliorer l'expérience Yaya (tableau de bord, historique) | 🟡 Moyenne |
| OF-10 | Ajouter la vue carte pour les matchings | 🟡 Moyenne |
| OF-11 | Développer l'administration avancée | 🟡 Moyenne |

### 2.2 Objectifs techniques

- Maintenir la cohérence avec le socle Django existant (FBV, HTMX, Tailwind)
- Garantir une couverture sécurité conforme aux standards OWASP
- Assurer la performance sur mobile (PWA, Lighthouse score > 80)
- Garantir la scalabilité pour une croissance de la base utilisateurs

### 2.3 Objectifs business

- Permettre l'activation des Formules Confort (149€/an) et Premium (199€/an)
- Augmenter la rétention des utilisateurs grâce aux notifications et au calendrier
- Réduire le churn par un suivi financier transparent pour les Yaya
- Assurer la conformité RGPD pour opérer légalement en Belgique/UE

---

## 3. Parties prenantes

| Partie | Rôle | Responsabilités |
|---|---|---|
| **Nyota Delecourt** | Commanditaire / Fondatrice | Validation fonctionnelle, décision produit |
| **Raphaël Jonard** | Développeur principal / Chef de projet technique | Architecture, développement, revue de code |
| **Luca Camilleri** | Développeur IT | Développement, intégration |
| **Digit-Up Agency** | Prestataire | Développement, conseil, audit |
| **Parents** | Utilisateurs finaux | Création de recherches, réservations |
| **Yaya** | Utilisateurs finaux | Création de propositions, gestion des accompagnements |

---

## 4. Périmètre du projet

### 4.1 Dans le périmètre (IN SCOPE)

- Corrections des bugs critiques identifiés dans l'audit
- Développement des 7 phases de fonctionnalités listées en section 7
- Migrations de base de données associées
- Tests unitaires et d'intégration par fonctionnalité
- Mise à jour de la documentation technique

### 4.2 Hors périmètre (OUT OF SCOPE)

- Développement d'une application mobile native (iOS / Android) — la PWA reste le canal mobile
- Refonte graphique du design system — les composants Tailwind existants sont conservés
- Migration vers un autre framework backend
- Développement d'une API REST publique (DRF)
- Intégration d'un outil CMS externe
- Développement de la fonctionnalité "Assurance enfant" (Formule Premium) — nécessite un partenariat assureur préalable

### 4.3 Fonctionnalités existantes maintenues

Les fonctionnalités suivantes sont **dans le périmètre de maintenance** uniquement (pas de refonte) :

- Inscription, connexion, MFA, OAuth Google
- Gestion du profil, des enfants, des adresses
- Création et gestion des trajets (propositions, recherches, récurrences)
- Moteur de matching géospatial
- Réservations (création, confirmation, annulation)
- Abonnements Stripe (après correction du bug)
- Vérification Stripe Identity
- Administration bana_admin
- Bug tracker interne

---

## 5. Architecture existante

### 5.1 Stack technique (référence)

| Composante | Technologie | Version |
|---|---|---|
| Backend | Django | 5.1.4 → cible 5.2 LTS |
| Base de données | PostgreSQL + PostGIS | — |
| Cache | LocMemCache → cible Redis | — |
| Temps réel | Django Channels + Daphne | 4.2.2 / 4.2.1 |
| Serveur WSGI | Gunicorn | 23.0.0 |
| Reverse proxy | Nginx | — |
| Frontend | Tailwind CSS + HTMX + JS Vanilla | — |
| Paiements | Stripe (abonnements + Identity) | SDK 12.3.0 |
| Géolocalisation | PostGIS + geopy (OpenStreetMap) | — |
| Auth | django-allauth | 65.7.0 |
| OS serveur | Debian 12 (OVH dédié) | — |

### 5.2 Apps Django existantes

`bana` · `accounts` · `trajects` · `chat` · `stripe_sub` · `bug_tracker` · `bana_admin` · `theme`

### 5.3 Modèles clés existants

`User` (Django) → `Profile` (O2O) → `Child`, `Languages`, `Review`, `FavoriteAddress`

`Traject` ← `ProposedTraject` / `ResearchedTraject` → `Reservation`

`Subscription` (Stripe) · `SiteVisit` · `Bug` / `BugComment` / `BugHistory`

---

## 6. Spécifications fonctionnelles — Existant à corriger

Ces corrections sont **préalables** à tout développement de nouvelles fonctionnalités. Elles doivent être livrées en priorité absolue.

---

### COR-01 — Correction bug Stripe : `stripe_customer_id` manquant

**Contexte :** Le fichier `stripe_sub/views.py` fait référence à `Profile.stripe_customer_id` pour retrouver l'utilisateur lors d'un renouvellement d'abonnement (`invoice.payment_succeeded`). Ce champ n'existe pas sur le modèle `Profile`. Résultat : tous les renouvellements automatiques échouent silencieusement.

**Solution retenue :**

Option A (recommandée) — Ajouter le champ sur `Profile` :
```python
# accounts/models.py
stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
```
Puis créer et appliquer la migration. La logique existante dans `_update_profile_customer_id()` et `invoice.payment_succeeded` fonctionnera sans autre modification.

Option B — Refactorer pour chercher via `Subscription` :
Modifier `_get_user_id_from_customer()` pour chercher `Subscription.objects.get(stripe_customer_id=customer_id)`.

**Critère d'acceptation :**
- Un abonnement Stripe arrivant à renouvellement est correctement mis à jour en base de données.
- Un webhook `invoice.payment_succeeded` est traité sans erreur dans les logs.

---

### COR-02 — Protection de la vue chat

**Contexte :** La vue `chat/views.py:index` n'a pas le décorateur `@login_required`. N'importe quel utilisateur non connecté peut accéder à la page `/chat/chat/`.

**Solution :**
```python
@login_required(login_url="/accounts/login/")
def index(request):
    return render(request, 'chat/index.html')
```

**Critère d'acceptation :**
- Un utilisateur non connecté accédant à `/chat/chat/` est redirigé vers la page de connexion.

---

### COR-03 — Configuration CORS

**Contexte :** `django-cors-headers` est installé mais aucune configuration `CORS_*` n'est présente dans `settings.py`. Le comportement CORS est indéterminé. `django-cors-middleware` (doublon) est également installé.

**Solution :**
```python
# settings.py
INSTALLED_APPS += ['corsheaders']
MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

CORS_ALLOWED_ORIGINS = [
    'https://bana.mobi',
    'https://www.bana.mobi',
]
```
Désinstaller `django-cors-middleware` (doublon inutile).

**Critère d'acceptation :**
- Les requêtes cross-origin depuis `bana.mobi` sont autorisées.
- Les requêtes depuis des origines inconnues sont bloquées.

---

### COR-04 — Activation de la bannière cookies

**Contexte :** Les fichiers `cookie-banner.css`, `cookie-banner.js` et `cookie-banner.html` sont créés mais non inclus dans les templates et non committés.

**Solution :**
1. Committer les fichiers existants.
2. Inclure `cookie-banner.html` dans `bana/templates/layouts/base.html` et `accounts/templates/allauth/layouts/base.html`.
3. Lier le fichier CSS dans les layouts.
4. Charger le JS en bas de page.

**Critère d'acceptation :**
- La bannière s'affiche à la première visite sur les deux layouts.
- Le consentement est mémorisé en `localStorage` ou cookie.
- Elle disparaît après acceptation/refus.

---

### COR-05 — Lien vers les CGU

**Contexte :** Le PDF des Conditions Générales d'Utilisation existe (`bana/static/bana/doc/conditions-generales-utilisation.pdf`) mais n'est lié nulle part dans les templates.

**Solution :**
- Ajouter un lien vers le PDF dans le footer (`layouts/footer.html`).
- Ajouter un lien "Conditions générales" sur la page d'inscription.

---

### COR-06 — Passage du cache vers Redis

**Contexte :** `LocMemCache` est incohérent en multi-worker Gunicorn (chaque worker a son propre espace mémoire). Redis est déjà disponible (channels_redis).

**Solution :**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

### COR-07 — Migration Django 5.2 LTS

**Contexte :** Django 5.1.4 n'est pas une version LTS. Django 5.2 LTS garantit un support jusqu'en avril 2028.

**Solution :**
```bash
pip install "Django>=5.2,<6.0"
python manage.py check
# Corriger les deprecation warnings
python manage.py test
```

**Critère d'acceptation :**
- `python manage.py check` sans warnings critiques.
- Toutes les fonctionnalités existantes opérationnelles après mise à jour.

---

### COR-08 — Personnalisation URL admin

**Contexte :** L'URL Django Admin est par défaut `/admin/` — vecteur d'attaque par brute force connu.

**Solution :**
```python
# bana/urls.py
path('bana-backoffice-2026/', admin.site.urls),
```

---

## 7. Spécifications fonctionnelles — Nouvelles fonctionnalités

---

## 7.1 Module Messagerie Temps Réel

### Contexte et objectif

L'infrastructure WebSocket (Django Channels + Daphne) est configurée mais aucun consumer n'est implémenté et le modèle `Message` n'existe pas. La messagerie est un prérequis fonctionnel absolu : sans elle, les parents et les Yaya ne peuvent pas se contacter avant un premier trajet.

---

### MSG-01 — Modèle de données Messagerie

**Nouveaux modèles à créer dans une app `chat` :**

```python
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optionnel : lien vers un matching ou une réservation
    related_reservation = models.ForeignKey(
        'trajects.Reservation', null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
```

**Migrations :** à générer et appliquer.

---

### MSG-02 — Consumer WebSocket authentifié

**Fichier :** `chat/consumers.py`

**Comportement attendu :**
- Connexion uniquement pour les utilisateurs authentifiés (`scope['user'].is_authenticated`).
- Un consumer par conversation (`ws/chat/<conversation_id>/`).
- À la connexion : rejoindre le groupe Channel de la conversation.
- À la réception d'un message JSON `{type: 'message', content: '...'}` :
  - Créer l'objet `Message` en base de données.
  - Broadcaster le message à tous les participants de la conversation via le groupe Channel.
- À la déconnexion : quitter le groupe.
- Gestion des erreurs : déconnexion propre si l'utilisateur n'est pas participant de la conversation.

**Routing :** `chat/routing.py`
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
```

**Intégration ASGI :** ajouter les routes WebSocket dans `bana/asgi.py`.

---

### MSG-03 — Vues et URLs REST de la messagerie

**URLs à créer dans `chat/urls.py` :**

| URL | Vue | Méthode | Description |
|---|---|---|---|
| `/chat/` | `conversation_list` | GET | Liste des conversations de l'utilisateur |
| `/chat/<id>/` | `conversation_detail` | GET | Détail + historique messages (paginé) |
| `/chat/start/<user_id>/` | `start_conversation` | POST | Démarrer une conversation avec un utilisateur |
| `/chat/<id>/mark-read/` | `mark_as_read` | POST | Marquer les messages comme lus |
| `/chat/unread-count/` | `unread_count` | GET (HTMX) | Nombre de messages non lus (badge) |

**Règles métier :**
- Une seule conversation par paire d'utilisateurs (vérifier avant création).
- Un utilisateur ne peut pas démarrer une conversation avec lui-même.
- L'accès à une conversation est limité aux participants.

---

### MSG-04 — Interface utilisateur messagerie

**Templates à créer :**

`chat/templates/chat/conversation_list.html` :
- Liste des conversations avec nom de l'interlocuteur, aperçu du dernier message, date, badge "non lu".
- Lien vers le détail de chaque conversation.
- Bouton "Nouvelle conversation" (à partir d'un profil utilisateur).

`chat/templates/chat/conversation_detail.html` :
- Historique des messages affichés en bulle (style SMS).
- Messages de l'utilisateur connecté à droite, messages de l'interlocuteur à gauche.
- Zone de saisie en bas avec bouton "Envoyer".
- Connexion WebSocket JavaScript : écoute des nouveaux messages + envoi.
- Pagination de l'historique (chargement des messages plus anciens au scroll).

**JavaScript :**
- `chat/static/chat/js/websocket.js` : gestion de la connexion WS, envoi/réception de messages, mise à jour du DOM en temps réel.

---

### MSG-05 — Badge messages non lus (header)

Le header app (`admin-header.html`) doit afficher un badge avec le nombre de messages non lus, rechargé via HTMX toutes les 30 secondes (ou via WebSocket si connecté).

```html
<span hx-get="/chat/unread-count/" hx-trigger="every 30s" hx-target="#unread-badge">
  <span id="unread-badge">0</span>
</span>
```

---

### MSG-06 — Lien messagerie depuis le profil et les matchings

- Sur la page profil public `/profil/utilisateur/<id>/` : ajouter un bouton "Envoyer un message".
- Sur les pages de matching detail : ajouter un bouton "Contacter" qui démarre ou reprend une conversation.

---

## 7.2 Module Notifications

### Contexte

Aucun email transactionnel n'est envoyé pour les actions métier (réservation, confirmation, matching). Les notifications sont pourtant listées comme incluses dans la Formule Essentiel ("Notifications nouveaux matchings", "Réservation des trajets").

---

### NOTIF-01 — Emails transactionnels

**Service email existant :** SMTP OVH configuré dans `settings.py`. Utiliser `django.core.mail.send_mail` ou `EmailMultiAlternatives` avec templates HTML.

**Créer le module `bana/notifications.py` :**

**Emails à implémenter :**

| Événement | Destinataire | Sujet | Contenu |
|---|---|---|---|
| Nouvelle réservation créée | Yaya | "Nouvelle demande de réservation" | Nom parent, trajet, date, lien vers détail |
| Réservation confirmée | Parent | "Votre réservation est confirmée" | Nom Yaya, trajet, date, heure |
| Réservation annulée | Parent + Yaya | "Réservation annulée" | Détails + raison si disponible |
| Nouveau matching trouvé | Utilisateur | "Nous avons trouvé un matching pour votre trajet" | Résumé matching, lien vers détail |
| Rappel trajet J-1 | Parent + Yaya | "Rappel : trajet demain" | Détails trajet + heure |
| Bienvenue (déjà existant) | Nouvel inscrit | — | Maintenir l'existant |
| Abonnement activé | Utilisateur | "Votre abonnement Bana est actif" | Période, prix, reçu |
| Abonnement expirant (J-7) | Utilisateur | "Votre abonnement expire dans 7 jours" | Lien de renouvellement |

**Structure recommandée des templates email :**
```
bana/templates/emails/
├── base_email.html          (layout commun : logo, footer désabonnement)
├── reservation_new.html
├── reservation_confirmed.html
├── reservation_cancelled.html
├── new_matching.html
├── trip_reminder.html
└── subscription_active.html
```

---

### NOTIF-02 — Notifications push Web (PWA)

**Contexte :** Le service worker est configuré. Les notifications push Web nécessitent le protocole **Web Push** (VAPID keys).

**Stack à implémenter :**
- Package Python : `pywebpush` ou `django-webpush`
- Génération des clés VAPID : à faire une fois en production
- Stockage des abonnements push : nouveau modèle `PushSubscription`

```python
# dans accounts/models.py ou nouveau fichier
class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'endpoint')
```

**Flux d'inscription push :**
1. Page profil : bouton "Activer les notifications push".
2. JavaScript appelle l'API Web Push du navigateur (`Notification.requestPermission()`).
3. L'abonnement push est envoyé en POST à `/notifications/subscribe/`.
4. La vue sauvegarde l'objet `PushSubscription`.

**Notifications push à envoyer :**
- Nouveau message reçu (depuis le consumer WebSocket)
- Nouvelle réservation (Yaya)
- Réservation confirmée (Parent)
- Rappel trajet J-1

---

### NOTIF-03 — Centre de préférences de notifications

Page dans le profil (`/profil/notifications/`) permettant à l'utilisateur de gérer ses préférences :

| Notification | Email | Push |
|---|---|---|
| Nouvelles réservations | ☑ | ☑ |
| Confirmations | ☑ | ☑ |
| Nouveaux matchings | ☑ | ☐ |
| Rappels trajets | ☑ | ☑ |
| Messages chat | ☐ | ☑ |
| Newsletter Bana | ☐ | ☐ |

Stockage dans un modèle `NotificationPreference` ou JSONField sur `Profile`.

---

## 7.3 Module Calendrier et Planification

### Contexte

Le calendrier est une fonctionnalité centrale de la **Formule Confort (149€/an)**. Sans lui, la Formule Confort ne peut pas être commercialisée.

---

### CAL-01 — Modèle de données Calendrier

Aucun nouveau modèle n'est strictement nécessaire : les données de trajets confirmés (`Reservation`, `ProposedTraject`, `ResearchedTraject`) fournissent les événements. Il faut cependant ajouter la notion d'**indisponibilité Yaya**.

```python
# trajects/models.py (nouveau modèle)
class YayaUnavailability(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unavailabilities')
    date_start = models.DateField()
    date_end = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date_start']
```

---

### CAL-02 — Vue Calendrier personnel

**URL :** `/trajets/calendrier/`

**Template :** `trajects/templates/trajects/calendrier/calendrier.html`

**Affichage :**
- Vue mensuelle (défaut) avec navigation mois précédent/suivant.
- Vue hebdomadaire (switch).
- Événements affichés sur le calendrier :
  - Trajets confirmés (couleur verte) — depuis `Reservation` status='confirmed'
  - Trajets en attente (couleur orange) — status='pending'
  - Indisponibilités Yaya (couleur rouge) — depuis `YayaUnavailability`
- Clic sur un événement : affiche un popover avec les détails (Yaya/Parent, horaires, lieu).

**Technologie calendrier :**
- Utiliser **FullCalendar.js** (version libre) ou une implémentation Tailwind/vanilla JS plus légère.
- Les événements sont chargés via un endpoint JSON `/trajets/calendrier/events/?start=...&end=...`.

**Endpoint JSON calendrier :**
```python
# trajects/views.py
@login_required
def calendar_events(request):
    """Retourne les événements du calendrier au format FullCalendar."""
    start = request.GET.get('start')
    end = request.GET.get('end')
    # Filtrer les réservations confirmées et en attente
    # Retourner JSON [{id, title, start, end, color, url}]
```

---

### CAL-03 — Gestion des indisponibilités Yaya

**URL :** `/trajets/calendrier/indisponibilites/`

Formulaire permettant au Yaya de :
- Ajouter une période d'indisponibilité (date début, date fin, raison optionnelle).
- Lister ses indisponibilités à venir.
- Supprimer une indisponibilité.

**Impact sur le matching :** Le moteur de matching (`find_matching_trajects`) doit exclure les `ProposedTraject` dont la date tombe dans une période d'indisponibilité du Yaya.

---

### CAL-04 — Rappels automatiques (J-1)

**Implémentation :** Management command `send_trip_reminders` à planifier via cron.

```bash
# crontab - exécuter chaque soir à 18h
0 18 * * * /chemin/vers/venv/bin/python /chemin/vers/bana/manage.py send_trip_reminders
```

**Logique :**
- Récupérer toutes les `Reservation` confirmées dont la date du `ProposedTraject` = demain.
- Envoyer un email et/ou push notification à chaque participant (Parent + Yaya).
- Logger les envois pour éviter les doublons.

---

### CAL-05 — Calendrier familial partagé (Formule Premium)

**Prérequis :** Module 7.10 (multi-utilisateurs) doit être implémenté en premier.

**Fonctionnalité :** Permettre à plusieurs membres d'une famille (ex: deux parents) de partager la même vue calendrier. Les événements de tous les membres de la famille sont agrégés.

**Implémentation :** Nouveau modèle `FamilyGroup` avec relation M2M vers `User`. La vue calendrier agrège les événements de tous les membres du groupe famille de l'utilisateur connecté.

---

## 7.4 Module Défraiement et Paiements Inter-Utilisateurs

### Contexte

Le défraiement est au cœur du modèle économique Bana : les Yaya reçoivent jusqu'à 176€/mois pour leurs trajets. Actuellement, le barème est affiché sur la page Tarifs mais **aucune logique de défraiement n'est implémentée**.

---

### DEF-01 — Modèle de données Défraiement

```python
# nouveau fichier payments/models.py
class DefraiementRate(models.Model):
    """Barème de référence (administrable)."""
    duration_min = models.IntegerField(help_text="Durée min en minutes")
    duration_max = models.IntegerField(null=True, blank=True, help_text="Durée max (null = illimité)")
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    effective_from = models.DateField()

    class Meta:
        ordering = ['duration_min']


class TripPayment(models.Model):
    """Défraiement associé à une réservation confirmée."""
    STATUS_CHOICES = [
        ('pending', 'En attente de versement'),
        ('paid', 'Versé'),
        ('disputed', 'Contesté'),
    ]
    reservation = models.OneToOneField('trajects.Reservation', on_delete=models.CASCADE)
    yaya = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='made_payments')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
```

---

### DEF-02 — Calcul automatique du défraiement

À la confirmation d'une réservation (`manage_reservation` action='confirm'), calculer automatiquement le montant de défraiement :

```python
def calculate_defraiement(reservation):
    """Calcule le défraiement selon la durée du trajet."""
    proposed = reservation.proposed_traject
    if proposed.departure_time and proposed.arrival_time:
        duration_minutes = (
            datetime.combine(date.today(), proposed.arrival_time) -
            datetime.combine(date.today(), proposed.departure_time)
        ).seconds // 60
        rate = DefraiementRate.objects.filter(
            duration_min__lte=duration_minutes,
            effective_from__lte=date.today()
        ).filter(
            Q(duration_max__isnull=True) | Q(duration_max__gte=duration_minutes)
        ).order_by('-effective_from').first()
        return rate.amount if rate else None
    return None
```

Un objet `TripPayment` est créé automatiquement lors de la confirmation.

---

### DEF-03 — Historique des paiements (Yaya)

**URL :** `/trajets/mes-revenus/`

**Template :** `trajects/templates/trajects/revenus/revenus.html`

**Affichage :**
- Total des revenus du mois en cours et de l'année.
- Liste paginée des trajets effectués avec : date, parent, montant, statut (en attente / versé).
- Filtres : par mois, par statut.
- Export CSV de l'historique.

---

### DEF-04 — Historique des paiements (Parent)

**URL :** `/trajets/mes-depenses/`

Symétrique à l'historique Yaya : liste des paiements effectués, total mensuel/annuel.

---

### DEF-05 — Confirmation de versement

Flux simplifié (phase 1 — sans Stripe Connect) :
- Le Parent marque un paiement comme "versé" manuellement.
- Le Yaya reçoit une notification de confirmation.
- L'admin peut voir tous les paiements et forcer les statuts.

**Phase 2 (future) — Stripe Connect :**
Intégrer Stripe Connect pour automatiser les versements Yaya. Ce point est identifié comme complexe et fera l'objet d'une spécification dédiée.

---

### DEF-06 — Reçus Yaya (PDF)

Générer un reçu PDF mensuel pour le Yaya récapitulant ses trajets et revenus, utilisable pour déclaration fiscale (activité d'appoint en Belgique).

**Technologie recommandée :** `WeasyPrint` ou `ReportLab`.

---

## 7.5 Module Sécurité et Confiance

### Contexte

La sécurité des enfants est la valeur centrale de Bana. Le flux de prise en charge et d'arrivée est décrit dans `work.html` mais non implémenté techniquement.

---

### SEC-01 — Confirmation de prise en charge

**Flux :**
1. Le jour d'un trajet, le Yaya voit dans son planning un bouton "Confirmer la prise en charge".
2. En cliquant (ou via push notification), il confirme avoir récupéré l'enfant.
3. Le Parent reçoit une notification : "📍 [Nom Yaya] a pris en charge [Prénom enfant] à [heure]".
4. L'heure de prise en charge est enregistrée sur la réservation.

**Nouveau champ sur `Reservation` :**
```python
pickup_confirmed_at = models.DateTimeField(null=True, blank=True)
arrival_confirmed_at = models.DateTimeField(null=True, blank=True)
```

**Vue :** `/trajets/réservations/<id>/confirmer-prise-en-charge/` (POST)

---

### SEC-02 — Confirmation d'arrivée

Identique à SEC-01 mais pour la dépose de l'enfant. Notification Parent : "✅ [Prénom enfant] est arrivé(e) à destination".

---

### SEC-03 — Signalement d'un utilisateur

**URL :** `/profil/<user_id>/signaler/` (modal sur la page profil public)

**Nouveau modèle :**
```python
class UserReport(models.Model):
    REASON_CHOICES = [
        ('behavior', 'Comportement inapproprié'),
        ('no_show', 'Absence non justifiée'),
        ('safety', 'Problème de sécurité'),
        ('other', 'Autre'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
```

**Admin bana_admin :** Nouveau tableau de bord pour traiter les signalements.

---

### SEC-04 — Blocage d'un utilisateur

**URL :** `/profil/<user_id>/bloquer/` (POST depuis page profil)

**Nouveau modèle :**
```python
class UserBlock(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_made')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
```

**Impact :** Les utilisateurs bloqués n'apparaissent pas dans les matchings et ne peuvent pas démarrer de conversation.

---

### SEC-05 — Restriction des avis aux trajets confirmés

**Contexte :** Actuellement, tout utilisateur connecté peut noter n'importe quel autre utilisateur. Il faut restreindre aux utilisateurs ayant partagé au moins un trajet confirmé.

**Modification de `profile_user` dans `accounts/views.py` :**
```python
# Avant d'autoriser la soumission d'un avis
shared_trip = Reservation.objects.filter(
    Q(user=request.user, proposed_traject__user=user, status='confirmed') |
    Q(user=user, proposed_traject__user=request.user, status='confirmed')
).exists()

allow_review = not is_own_profile and not existing_review and shared_trip
```

---

### SEC-06 — Modération des avis

**Nouveau champ sur `Review` :**
```python
is_published = models.BooleanField(default=True)
is_flagged = models.BooleanField(default=False)
flag_reason = models.TextField(blank=True)
```

**Fonctionnalité admin :** Interface bana_admin pour voir les avis signalés et les masquer.

---

## 7.6 Module RGPD et Conformité

### Contexte légal

En tant que plateforme traitant des données de mineurs (enfants) et de localisation, BanaCommunity est soumise au RGPD (Règlement Général sur la Protection des Données) et doit se conformer aux exigences belges de l'APD (Autorité de Protection des Données).

---

### RGPD-01 — Bannière cookie conforme (COR-04 étendu)

La bannière doit permettre un **consentement granulaire** par catégorie :

| Catégorie | Description | Obligatoire |
|---|---|---|
| Fonctionnels | Session, authentification, langue | Oui |
| Analytiques | `SiteVisitMiddleware` | Non (opt-in) |
| Marketing | Aucun actuellement | Non |

**Stockage du consentement :** cookie `bana_consent` avec JSON `{functional: true, analytics: false, marketing: false}` + durée 12 mois.

**Impact sur SiteVisitMiddleware :** n'enregistrer les visites que si `analytics: true`.

---

### RGPD-02 — Page Politique de Confidentialité

**URL :** `/fr/politique-de-confidentialite/`

Contenu obligatoire :
- Identité du responsable de traitement (Bana ASBL/SRL)
- Données collectées et finalités
- Durées de conservation
- Droits des personnes (accès, rectification, effacement, portabilité, limitation, opposition)
- Coordonnées DPO ou contact RGPD
- Transferts de données hors UE (Stripe — USA, serveurs OVH — EU)
- Sous-traitants (Stripe, Google OAuth, OpenStreetMap)

**Lien :** depuis le footer, la page d'inscription, et la bannière cookie.

---

### RGPD-03 — Export des données personnelles (Droit à la portabilité)

**URL :** `/profil/mes-donnees/` → bouton "Télécharger mes données"

**Vue :** génère un fichier JSON ou ZIP contenant :
- Données User (nom, email, date inscription)
- Profile (photo, bio, adresses, langues, modes de transport)
- Enfants enregistrés
- Trajets créés (proposés et recherchés)
- Réservations
- Avis donnés et reçus
- Conversations et messages (export texte)

**Délai de génération :** si le volume est important, générer en tâche asynchrone et envoyer par email.

---

### RGPD-04 — Suppression complète des données (Droit à l'effacement)

**URL :** `/profil/supprimer-mon-compte/` (POST avec confirmation mot de passe)

**Flux :**
1. L'utilisateur demande la suppression de son compte.
2. Création d'une `AccountDeletionRequest` avec statut "pending" et délai de 30 jours.
3. Email de confirmation avec lien d'annulation (valable 7 jours).
4. Après 30 jours sans annulation : suppression en cascade de toutes les données ou anonymisation.

**Anonymisation vs suppression :**
- Les `Reservation` confirmées sont **anonymisées** (user_id = None, données personnelles effacées) pour maintenir l'intégrité historique des trajets.
- Les messages sont supprimés.
- Le profil, les enfants, les avis sont supprimés.

---

### RGPD-05 — Registre des traitements (interne)

Document à produire (hors développement) listant :
- Traitements des données personnelles
- Finalités
- Bases légales (consentement, contrat, intérêt légitime)
- Durées de conservation
- Mesures de sécurité

---

## 7.7 Module Expérience Yaya

### YAY-01 — Tableau de bord Yaya

**URL :** `/trajets/mon-tableau-de-bord/` (accessible aux Yaya uniquement)

**Contenu :**
- **KPIs du mois :** nombre de trajets effectués, revenus totaux, note moyenne reçue.
- **Prochains trajets :** 5 prochains trajets confirmés avec horaire et parent.
- **Réservations en attente :** demandes à traiter.
- **Nouveaux matchings :** derniers matchings non consultés.

---

### YAY-02 — Déclaration d'indisponibilité

(Voir CAL-03 — géré dans le module Calendrier)

---

### YAY-03 — Profil Yaya enrichi

Ajouter sur le profil public des Yaya :
- **Zones de couverture :** liste des communes/quartiers où le Yaya est disponible.
- **Tranches horaires de disponibilité :** affichage indicatif (matin, midi, après-midi, soir).
- **Badge de vérification :** affichage visuel du niveau de vérification (CI ✅, BVM ✅, Profil ✅).
- **Nombre de trajets effectués** (depuis `trips_count`).

---

### YAY-04 — Évaluation bidirectionnelle

**Contexte :** Actuellement, seuls les utilisateurs peuvent noter d'autres utilisateurs librement. Mettre en place une évaluation **post-trajet** déclenchée automatiquement.

**Flux :**
1. 24h après un trajet confirmé et passé, un email/push est envoyé à chaque partie.
2. "Comment s'est passé le trajet avec [Nom] ? Laissez un avis."
3. Lien vers le formulaire d'avis pré-rempli avec la réservation concernée.
4. L'avis est publié après modération (ou immédiatement si pas de modération active).

---

## 7.8 Module Recherche Avancée et Cartographie

### MAP-01 — Vue carte des matchings

**URL :** `/trajets/carte/`

**Technologie recommandée :** Leaflet.js (open source) + tuiles OpenStreetMap (gratuit).

**Affichage :**
- Points de départ et d'arrivée des trajets proposés dans un rayon de 50 km autour de l'utilisateur.
- Cluster de points pour éviter la surcharge.
- Popup au clic : résumé du trajet + lien vers le matching detail.
- Filtre : mode de transport, horaire.

**Endpoint :** `/trajets/carte/geojson/` retourne un GeoJSON des `ProposedTraject` actifs.

---

### MAP-02 — Filtres avancés de matching

Ajouter sur les pages de matching des filtres supplémentaires :
- Distance maximale au point de départ (slider)
- Créneau horaire (heure min / heure max)
- Note minimale du Yaya (étoiles)
- Mode de transport spécifique

Ces filtres s'appliquent en HTMX (sans rechargement de page).

---

### MAP-03 — Notifications automatiques de nouveaux matchings

**Contexte :** La Formule Essentiel inclut "Notifications nouveaux matchings". À implémenter via la management command `notify_new_matchings` (cron quotidien).

**Logique :**
- Pour chaque `ProposedTraject` ou `ResearchedTraject` actif et récent (créé dans les 24h) :
  - Lancer le moteur de matching
  - Si des matchings sont trouvés et que l'utilisateur n'a pas été notifié récemment pour ce trajet
  - Envoyer un email et/ou push "Nouveau matching trouvé !"

---

## 7.9 Module Administration Avancée

### ADM-01 — Dashboard business

**URL :** `/bana_admin/dashboard/`

**KPIs à afficher :**
- Revenus Stripe du mois (via API Stripe)
- Nombre d'abonnements actifs (Parent / Yaya)
- Taux de conversion (inscrits → abonnés)
- Nombre de trajets matchés / réservés / confirmés
- Taux d'abandon réservation
- Utilisateurs actifs (30 derniers jours)

---

### ADM-02 — Export CSV/Excel

**Dans les vues admin existantes :**
- Export des membres (nom, email, service, date inscription, statut vérification)
- Export des réservations (avec montants de défraiement)
- Export des abonnements Stripe

**Technologie :** `csv` module Python (built-in) ou `openpyxl` pour Excel.

---

### ADM-03 — Gestion des signalements

(Voir SEC-03 — interface dans bana_admin)

**URL :** `/bana_admin/signalements/`

- Liste des signalements non traités
- Détail du signalement + lien vers les profils
- Actions : "Résolu" / "Compte suspendu" / "Avertissement envoyé"

---

### ADM-04 — Workflow de validation BVM simplifié

**Contexte :** La validation BVM est actuellement un simple bouton dans une liste de profils. Un workflow plus structuré est nécessaire.

**Amélioration :**
- File d'attente des BVM à valider (triés par date de dépôt)
- Visualisation du document BVM directement dans l'interface
- Commentaire de refus avec email automatique au membre
- Log d'audit de toutes les validations (qui a validé quoi et quand)

---

### ADM-05 — Outil emailing groupé

**URL :** `/bana_admin/emails/`

Interface minimaliste pour envoyer un email à un segment d'utilisateurs :
- Tous les membres
- Tous les Parents
- Tous les Yaya
- Membres sans abonnement actif

**Champs :** Sujet, corps HTML (éditeur simple), aperçu avant envoi, confirmation.

---

## 7.10 Module Multi-utilisateurs (Formule Premium)

### MULTI-01 — Groupe Famille

**Nouveau modèle :**
```python
class FamilyGroup(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_family')
    members = models.ManyToManyField(User, related_name='family_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner',)  # un seul groupe famille par propriétaire
```

**Fonctionnalités :**
- Inviter un membre par email (`/profil/famille/inviter/`)
- Accepter/refuser une invitation
- Quitter un groupe famille
- Le propriétaire peut retirer un membre

---

### MULTI-02 — Partage des enfants dans le groupe famille

Les enfants du compte Parent peuvent être accessibles aux membres de son groupe famille pour créer des `ResearchedTraject`.

**Permission :** Un membre du groupe famille peut créer des trajets au nom des enfants de n'importe quel membre du groupe.

---

### MULTI-03 — Vue calendrier partagée

(Voir CAL-05)

---

## 8. Spécifications techniques

### 8.1 Conventions de développement

- **Pattern de vues :** FBV (`@login_required`, `@require_http_methods`) — conserver la cohérence avec le code existant.
- **HTMX :** pour toutes les interactions partielles (filtres, formulaires inline, badges).
- **Templates :** Tailwind CSS avec les classes existantes. Pas de nouveau framework CSS.
- **Nouvelles apps :** créer une app `payments` pour le module défraiement. Étendre `chat` pour la messagerie.
- **JavaScript :** Vanilla JS ou ajout ciblé de bibliothèques (Leaflet, FullCalendar) — pas de React/Vue.
- **Tests :** écrire des tests unitaires pour chaque nouvelle vue et fonction métier critique.

### 8.2 Conventions ORM

- Toujours utiliser `select_related()` / `prefetch_related()` sur les querysets liés.
- `@transaction.atomic` sur les vues qui modifient plusieurs modèles.
- Agrégations conditionnelles via `Count('id', filter=Q(...))`.
- Ne jamais utiliser `_` comme variable muette dans `trajects/views.py` (conflit avec `gettext_lazy`).

### 8.3 Sécurité des nouvelles vues

- Chaque vue `@login_required` doit vérifier que l'objet accédé appartient bien à l'utilisateur connecté (pas de IDOR).
- Les WebSocket consumers doivent vérifier `scope['user'].is_authenticated` et la participation à la conversation.
- Les uploads de fichiers doivent valider le type MIME côté serveur (pas uniquement l'extension).
- Les exports de données personnelles doivent être accessibles uniquement au propriétaire des données.

### 8.4 Performance

- Les vues de liste doivent être paginées (20 éléments par défaut).
- Les endpoints JSON/GeoJSON pour la carte doivent être mis en cache Redis (TTL 5 minutes).
- Les emails transactionnels doivent être envoyés en tâche asynchrone (Celery ou thread dédié) pour ne pas bloquer la réponse HTTP.
- Les notifications push doivent être groupées pour éviter les envois en masse bloquants.

### 8.5 Infrastructure

| Composante | Actuelle | Cible |
|---|---|---|
| Django | 5.1.4 | 5.2 LTS |
| Cache | LocMemCache | Redis (instance existante) |
| Emails async | Synchrone | Thread ou Celery |
| PDF | Absent | WeasyPrint |
| Maps | Absent | Leaflet.js + OSM |
| Calendrier | Absent | FullCalendar.js (ou équivalent) |
| Push | Absent | Web Push API + pywebpush |

### 8.6 Variables d'environnement à ajouter

```env
# Clés VAPID pour Web Push
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_ADMIN_EMAIL=contact@bana.mobi

# Redis (si séparé de Channels)
REDIS_URL=redis://127.0.0.1:6379/1

# Stripe Connect (Phase 5)
STRIPE_CONNECT_CLIENT_ID=...
```

---

## 9. Contraintes et exigences transversales

### 9.1 Sécurité

- Toute nouvelle fonctionnalité doit passer le checklist OWASP Top 10.
- Les données des enfants ne doivent jamais être exposées à des utilisateurs non liés.
- Les fichiers uploadés (BVM, pièces jointes) doivent être stockés hors du répertoire web public.
- Le webhook Stripe doit rester hors `i18n_patterns` et hors `@login_required`.
- Les tokens de confirmation email ont une durée de vie de 3 jours (déjà configuré).

### 9.2 Accessibilité

- Respecter les critères WCAG 2.1 niveau AA pour les nouvelles pages.
- Contraste suffisant sur les indicateurs de statut colorés (réservations, matchings).
- Formulaires avec labels explicites et messages d'erreur accessibles.

### 9.3 Internationalisation

- Toutes les chaînes utilisateur doivent être wrappées dans `_()` ou `gettext_lazy()`.
- Exécuter `makemessages` et `compilemessages` après chaque nouveau template.
- Les emails transactionnels doivent respecter la langue de l'utilisateur.

### 9.4 Mobile

- Toutes les nouvelles pages doivent être responsives (mobile-first).
- La vue calendrier doit être utilisable sur mobile (scroll, tap sur événements).
- La messagerie doit fonctionner correctement sur mobile (clavier virtuel, scroll de l'historique).

### 9.5 RGPD

- Toute nouvelle donnée collectée doit être documentée dans le registre de traitements.
- Les données des enfants sont des données sensibles (mineurs) — traitement minimal.
- Les logs d'accès ne doivent pas contenir d'informations personnelles non chiffrées.
- La durée de conservation des messages doit être définie et documentée.

---

## 10. Maquettes fonctionnelles (description)

*Les maquettes visuelles (wireframes/mockups) sont à produire séparément par le designer UI. Les descriptions ci-dessous définissent la structure fonctionnelle attendue.*

### Page Messagerie — Liste des conversations
```
┌─────────────────────────────────────────────────┐
│ ← Mes messages                    [+ Nouveau]   │
├─────────────────────────────────────────────────┤
│ [Photo] Marie D.          Aujourd'hui 14:32  🔴 │
│         "D'accord pour mardi..."                │
├─────────────────────────────────────────────────┤
│ [Photo] Jean-Pierre M.    Hier 09:15            │
│         "Merci pour le trajet !"                │
├─────────────────────────────────────────────────┤
│ [Photo] Aminata K.        12 juin               │
│         "Parfait, à demain alors"               │
└─────────────────────────────────────────────────┘
```

### Page Messagerie — Conversation
```
┌─────────────────────────────────────────────────┐
│ ← Marie D.        [CI ✅] [BVM ✅]   [Profil →] │
├─────────────────────────────────────────────────┤
│                                                 │
│ [Bonjour, votre trajet me convient bien]  14:30 │
│                                                 │
│ 14:31  [Super ! On se retrouve à quelle heure?] │
│                                                 │
│ [Je serai là à 7h45 devant l'école]       14:32 │
│                                                 │
├─────────────────────────────────────────────────┤
│ [                           Message...    ] [→] │
└─────────────────────────────────────────────────┘
```

### Page Calendrier mensuel
```
┌─────────────────────────────────────────────────┐
│ ← Juin 2026                      [Mois][Semaine]│
├───┬───┬───┬───┬───┬───┬───────────────────────┤
│Lu │Ma │Me │Je │Ve │Sa │Di                       │
├───┼───┼───┼───┼───┼───┼───┬─────────────────   │
│   │   │   │   │ 5 │ 6 │ 7 │                    │
│   │   │   │   │🟢 │   │   │                    │
│   │   │   │   │7h30│   │   │                    │
├───┼───┼───┼───┼───┼───┼───┤                    │
│ 8 │ 9 │10 │11 │12 │13 │14 │                    │
│🟠 │   │🟢 │   │🟢 │   │   │                    │
└───┴───┴───┴───┴───┴───┴───┘                    │
 🟢 Confirmé  🟠 En attente  🔴 Indispo            │
└─────────────────────────────────────────────────┘
```

### Tableau de bord Yaya
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Ce mois     │ │  Revenus     │ │  Ma note     │
│  12 trajets  │ │  54,00 €     │ │  ★★★★☆ 4.2  │
└──────────────┘ └──────────────┘ └──────────────┘

Prochains trajets
┌─────────────────────────────────────────────────┐
│ Demain — 7h45 → École Victor Hugo               │
│ Lucas M. (Parent) · Voiture · 1 enfant          │
│ [Confirmer prise en charge]   [Voir détail →]   │
├─────────────────────────────────────────────────┤
│ Lundi 22 juin — 8h00 → École Saint-Nicolas      │
│ Sophie D. (Parent) · Vélo · 2 enfants           │
└─────────────────────────────────────────────────┘
```

---

## 11. Phasage et Planning

### Phase 0 — Corrections critiques
**Durée estimée :** 2-3 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| COR-01 | Correction bug stripe_customer_id | S |
| COR-02 | Login required vue chat | XS |
| COR-03 | Configuration CORS | XS |
| COR-04 | Activation bannière cookies | S |
| COR-05 | Lien CGU dans templates | XS |
| COR-06 | Cache Redis | S |
| COR-07 | Migration Django 5.2 LTS | M |
| COR-08 | Personnalisation URL admin | XS |

---

### Phase 1 — Messagerie temps réel
**Durée estimée :** 6-8 semaines · 1-2 développeurs

| Réf. | Tâche | Complexité |
|---|---|---|
| MSG-01 | Modèles Conversation, Message, MessageReadStatus | S |
| MSG-02 | Consumer WebSocket authentifié | M |
| MSG-03 | Vues et URLs (liste, détail, démarrer, mark-read) | M |
| MSG-04 | Templates (liste conversations, conversation détail) | M |
| MSG-05 | Badge messages non lus (header HTMX) | S |
| MSG-06 | Boutons "Contacter" sur profil et matchings | S |

---

### Phase 2 — Notifications
**Durée estimée :** 4-6 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| NOTIF-01 | Module emails transactionnels (7 emails) | M |
| NOTIF-02 | Push notifications Web (VAPID, PushSubscription) | L |
| NOTIF-03 | Centre préférences notifications | S |

---

### Phase 3 — Calendrier et Planification
**Durée estimée :** 6-8 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| CAL-01 | Modèle YayaUnavailability + migration | S |
| CAL-02 | Vue calendrier (mensuelle/hebdomadaire) + endpoint JSON | L |
| CAL-03 | Gestion indisponibilités Yaya | M |
| CAL-04 | Management command rappels J-1 + cron | M |
| CAL-05 | Calendrier familial partagé (dépend Phase 7) | M |

---

### Phase 4 — Défraiement et Paiements
**Durée estimée :** 6-8 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| DEF-01 | Modèles DefraiementRate, TripPayment | S |
| DEF-02 | Calcul automatique à la confirmation de réservation | M |
| DEF-03 | Historique revenus Yaya (liste + export CSV) | M |
| DEF-04 | Historique dépenses Parent | M |
| DEF-05 | Confirmation versement (flux manuel) | S |
| DEF-06 | Reçus PDF mensuels Yaya | M |

---

### Phase 5 — Sécurité et Confiance
**Durée estimée :** 4-5 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| SEC-01 | Confirmation prise en charge enfant | M |
| SEC-02 | Confirmation arrivée enfant | S |
| SEC-03 | Signalement utilisateur + admin interface | M |
| SEC-04 | Blocage utilisateur | M |
| SEC-05 | Restriction avis aux trajets confirmés | S |
| SEC-06 | Modération des avis | S |

---

### Phase 6 — RGPD et Conformité
**Durée estimée :** 4-5 semaines · 1 développeur

| Réf. | Tâche | Complexité |
|---|---|---|
| RGPD-01 | Bannière cookie granulaire | M |
| RGPD-02 | Page politique de confidentialité | S (contenu à fournir) |
| RGPD-03 | Export données personnelles JSON | M |
| RGPD-04 | Suppression complète (30 jours + email confirmation) | L |

---

### Phase 7 — Expérience avancée et Administration
**Durée estimée :** 8-10 semaines · 1-2 développeurs

| Réf. | Tâche | Complexité |
|---|---|---|
| YAY-01 | Tableau de bord Yaya | M |
| YAY-03 | Profil Yaya enrichi | S |
| YAY-04 | Évaluation post-trajet automatique | M |
| MAP-01 | Vue carte des matchings (Leaflet) | L |
| MAP-02 | Filtres avancés matching (HTMX) | M |
| MAP-03 | Notifications automatiques nouveaux matchings (cron) | M |
| ADM-01 | Dashboard business | M |
| ADM-02 | Export CSV/Excel | M |
| ADM-04 | Workflow validation BVM | M |
| ADM-05 | Outil emailing groupé | M |
| MULTI-01/02 | Groupe famille + partage enfants | L |

---

### Récapitulatif planning

| Phase | Périmètre | Durée estimée |
|---|---|---|
| Phase 0 | Corrections critiques | 2-3 semaines |
| Phase 1 | Messagerie temps réel | 6-8 semaines |
| Phase 2 | Notifications | 4-6 semaines |
| Phase 3 | Calendrier | 6-8 semaines |
| Phase 4 | Défraiement | 6-8 semaines |
| Phase 5 | Sécurité & Confiance | 4-5 semaines |
| Phase 6 | RGPD | 4-5 semaines |
| Phase 7 | Expérience avancée | 8-10 semaines |
| **Total** | **~50 fonctionnalités** | **~40-53 semaines** |

*Légende complexité : XS (<1j) · S (1-2j) · M (3-5j) · L (1-2sem)*

---

## 12. Livrables

### Par phase

| Phase | Livrables techniques | Livrables documentaires |
|---|---|---|
| Phase 0 | Code corrigé, migrations | Rapport de tests, changelog |
| Phase 1 | App chat complète, consumers WS | Doc technique WebSocket |
| Phase 2 | Module notifications, templates email | Guide de configuration VAPID |
| Phase 3 | Module calendrier, cron J-1 | Guide crontab prod |
| Phase 4 | App payments, PDFs | Guide fiscal Yaya |
| Phase 5 | Vues sécurité, modèles | — |
| Phase 6 | Module RGPD complet | Registre de traitements |
| Phase 7 | Dashboard, carte, admin | Guide d'administration |

### Livrables transversaux

- Code source versionné (Git) avec branches par phase
- Fichier `requirements.txt` mis à jour
- Migrations Django validées
- `CLAUDE.md` mis à jour avec les nouvelles conventions
- Recette de déploiement par phase

---

## 13. Critères d'acceptation

### Critères généraux (toutes les phases)

| Critère | Condition |
|---|---|
| **Fonctionnel** | La fonctionnalité fonctionne comme décrite dans les specs sur les navigateurs cibles (Chrome, Firefox, Safari mobile) |
| **Sécurité** | Aucune donnée d'un utilisateur n'est accessible à un autre utilisateur non autorisé |
| **Performance** | Les pages se chargent en moins de 3 secondes sur une connexion 4G |
| **Mobile** | Les nouvelles pages sont utilisables sur iPhone SE (375px) et Galaxy S21 (360px) |
| **i18n** | Toutes les chaînes sont traduisibles (wrappées dans `_()`) |
| **Pas de régression** | Les fonctionnalités existantes ne sont pas cassées |

### Critères spécifiques par module

**Messagerie :**
- Un message envoyé par le Yaya apparaît chez le Parent en moins de 500ms (WS connecté).
- Un message envoyé alors que le destinataire est offline est reçu à la prochaine connexion.
- Le badge de messages non lus est exact.

**Notifications email :**
- L'email de réservation est envoyé dans les 60 secondes suivant la création.
- L'email respecte la langue de l'utilisateur.
- Le lien de désabonnement fonctionne.

**Calendrier :**
- Les événements du calendrier sont exacts (aucun trajet manquant, aucun trajet fantôme).
- La navigation mois précédent/suivant fonctionne sans rechargement de page.

**Défraiement :**
- Le montant calculé correspond au barème en vigueur à la date du trajet.
- L'export CSV contient toutes les lignes de la période sélectionnée.

**RGPD :**
- L'export de données personnelles contient toutes les données de l'utilisateur.
- La suppression de compte déclenche bien un email de confirmation et un délai de 30 jours.
- Après suppression, les données personnelles ne sont plus accessibles via l'interface.

**Paiements Stripe (COR-01) :**
- Un webhook `invoice.payment_succeeded` met bien à jour l'abonnement en base de données.
- Un abonnement expiré est bien désactivé après le délai de grâce Stripe.

---

## 14. Glossaire

| Terme | Définition |
|---|---|
| **Parent** | Utilisateur de la plateforme cherchant un accompagnement pour ses enfants |
| **Yaya** | Adulte de confiance proposant d'accompagner des enfants pour des trajets |
| **Trajet** | Entité géographique (adresse départ → adresse arrivée) avec coordonnées PostGIS |
| **ProposedTraject** | Offre d'accompagnement créée par un Yaya ou un Parent |
| **ResearchedTraject** | Demande d'accompagnement créée par un Parent |
| **Matching** | Correspondance entre un `ProposedTraject` et un `ResearchedTraject` détectée par le moteur géospatial |
| **Réservation** | Demande formelle d'un Parent pour un trajet proposé par un Yaya |
| **BVM** | Bonne Vie et Mœurs — extrait 596.2 du casier judiciaire belge |
| **CI** | Carte d'Identité — vérifiée via Stripe Identity |
| **Défraiement** | Compensation financière versée par le Parent au Yaya pour un trajet effectué |
| **Formule Essentiel** | Abonnement Parent à 99€/an |
| **Formule Confort** | Abonnement Parent à 149€/an (inclut calendrier, rappels, historique) |
| **Formule Premium** | Abonnement Parent à 199€/an (inclut multi-utilisateurs, badge enfant) |
| **groupe_uid** | UUID identifiant un groupe de trajets récurrents (ProposedTraject ou ResearchedTraject) |
| **is_simple** | ProposedTraject sans destination fixe — matching par rayon uniquement (trajets Yaya rayon) |
| **HTMX** | Bibliothèque JavaScript permettant des requêtes AJAX déclaratives via attributs HTML |
| **PostGIS** | Extension PostgreSQL pour les données géospatiales |
| **Channels** | Extension Django pour les WebSockets et le temps réel |
| **RGPD** | Règlement Général sur la Protection des Données (UE 2016/679) |
| **APD** | Autorité de Protection des Données — régulateur belge |
| **VAPID** | Voluntary Application Server Identification — protocole d'authentification Web Push |

---

*Document généré par Digit-Up Agency — Tous droits réservés*
*Ce cahier des charges est un document de travail. Il doit être validé par le commanditaire avant d'être utilisé comme base contractuelle.*
