# 00 — Synthèse Audit Applicatif
**Projet :** BanaCommunity (bana.mobi)
**Commanditaire :** Raphaël Jonard — Digit-Up Agency
**Auditeur :** Analyste Fonctionnel Senior — Digit-Up Agency
**Date :** 2026-06-19

---

## 1. Fiche d'identité du projet

| Élément | Valeur |
|---|---|
| **Nom du projet** | BanaCommunity |
| **Domaine** | bana.mobi |
| **Stack** | Django 5.1.4 · Python · PostgreSQL + PostGIS · Redis · Gunicorn + Daphne · Nginx |
| **Hébergement** | Serveur dédié OVH — Debian 12 |
| **Framework CSS** | Tailwind CSS (django-tailwind) |
| **JS** | Vanilla JS + HTMX |
| **Auth** | django-allauth (email, Google OAuth, MFA TOTP + WebAuthn) |
| **Paiement** | Stripe (abonnements + Stripe Identity) |
| **Géolocalisation** | PostGIS + geopy (OpenStreetMap) |
| **Temps réel** | Django Channels 4 + Daphne (WebSocket) |
| **Nombre d'apps** | 8 apps Django |
| **Nombre de modèles** | 18 modèles |
| **Nombre de templates** | ~95 fichiers HTML |
| **Nombre de vues** | ~93 fonctions/classes |
| **Migrations** | Toutes appliquées (0 en attente) |
| **Langues** | Français (défaut), Anglais, Néerlandais |

---

## 2. Résumé Exécutif

BanaCommunity est une plateforme communautaire d'accompagnement des enfants (covoiturage scolaire et Yaya) développée en Django 5.1.4. L'architecture est solide : FBV systématiques, HTMX pour les interactions partielles, PostGIS pour le matching géospatial, Stripe pour les paiements et la vérification d'identité.

Le code est bien structuré et suit les conventions Django. Les aspects sécurité Django sont globalement corrects en production (HSTS, cookies sécurisés, SECRET_KEY externalisée). Le moteur de matching géospatial est fonctionnel avec pré-filtre PostGIS à 50 km et affinement Python.

Cependant, plusieurs **anomalies fonctionnelles critiques** ont été identifiées : le champ `stripe_customer_id` manquant sur le modèle `Profile` compromet le renouvellement automatique des abonnements, l'app `chat` est non protégée et sans persistence, et CORS est installé mais non configuré. L'app de messagerie est en état prototype. Le budget technique restant à couvrir (mensuration, calendrier, notifications push, messagerie complète) est significatif.

---

## 3. Matrice des Risques Sécurité

| ID | Finding | Criticité | Impact | Effort fix |
|---|---|---|---|---|
| S01 | Vue chat sans authentification | 🔴 Critique | Accès non authentifié à la page chat | Faible (1 décorateur) |
| S02 | `stripe_customer_id` absent sur Profile | 🔴 Critique | Renouvellements abonnement silencieusement ratés | Moyen (migration + correction logique) |
| S03 | CORS non configuré | 🔴 Critique | Comportement CORS indéterminé | Faible (3 lignes settings) |
| S04 | URL admin `/admin/` par défaut | ⚠️ Modéré | Vecteur d'attaque connu (brute force) | Faible |
| S05 | Django 5.1.4 non-LTS | ⚠️ Modéré | Fin de support plus proche que 5.2 LTS | Moyen (tests de régression) |
| S06 | `\|safe` sur textes statiques | ⚠️ Faible | Risque si textes deviennent éditables | Faible |
| S07 | Cache LocMemCache multi-worker | ⚠️ Modéré | Incohérence cache entre workers Gunicorn | Faible (config Redis) |
| S08 | Port Daphne 8001 potentiellement exposé | ⚠️ À vérifier | Accès WebSocket non proxifié | À vérifier sur serveur |

---

## 4. Recommandations Prioritaires

### P1 — Corriger le bug Stripe (critique, effort moyen)
Ajouter `stripe_customer_id = models.CharField(...)` sur `Profile` + migration, ou refactorer la logique dans `stripe_sub/views.py` pour chercher le `stripe_customer_id` sur `Subscription` (qui le possède déjà). Sans ce correctif, les renouvellements automatiques échouent.

### P2 — Protéger la vue chat (critique, effort faible)
Ajouter `@login_required` sur `chat/views.py:index`. Implémenter les consumers WebSocket avec authentification.

### P3 — Configurer CORS explicitement (critique, effort faible)
Ajouter dans `settings.py` :
```python
CORS_ALLOWED_ORIGINS = ['https://bana.mobi', 'https://www.bana.mobi']
```
Et supprimer le doublon `django-cors-middleware`.

### P4 — Migrer vers Django 5.2 LTS (modéré, effort moyen)
Django 5.2 LTS garantit un support étendu. La migration depuis 5.1.4 est mineure (patch version bump).

### P5 — Passer le cache en Redis (modéré, effort faible)
Redis est déjà disponible (channels_redis). Remplacer `LocMemCache` par `RedisCache` pour avoir un cache cohérent en multi-worker :
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## 5. Table des matières

| Document | Contenu |
|---|---|
| [01_INVENTAIRE_FONCTIONNEL.md](./01_INVENTAIRE_FONCTIONNEL.md) | Inventaire complet des apps, modèles, vues, formulaires, signals, commands, intégrations |
| [02_CARTOGRAPHIE_INTERFACES.md](./02_CARTOGRAPHIE_INTERFACES.md) | Sitemap fonctionnel, inventaire templates, composants JS, responsive |
| [03_MODELISATION_DATABASE.md](./03_MODELISATION_DATABASE.md) | Dictionnaire de données, diagramme ER Mermaid, état migrations, index, anomalies |
| [04_AUDIT_SECURITE.md](./04_AUDIT_SECURITE.md) | Grille sécurité Django, injections SQL/XSS, contrôle d'accès, dépendances, findings |
| [05_ANALYSE_FONCTIONNELLE.md](./05_ANALYSE_FONCTIONNELLE.md) | Fonctionnalités existantes vs manquantes — cahier des charges pour devis |
