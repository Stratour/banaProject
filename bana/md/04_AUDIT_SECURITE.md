# 04 — Audit de Sécurité
**Projet :** BanaCommunity (bana.mobi)
**Auditeur :** Analyste Fonctionnel Senior — Digit-Up Agency
**Date :** 2026-06-19

---

## 4A — Sécurité Applicative (Django)

### `python manage.py check --deploy` (exécuté en contexte local, DEBUG=True)
```
WARNINGS:
W004 SECURE_HSTS_SECONDS non défini
W008 SECURE_SSL_REDIRECT non défini
W012 SESSION_COOKIE_SECURE non défini
W016 CSRF_COOKIE_SECURE non défini
W018 DEBUG = True
```
Ces warnings sont **attendus** en dev local. Ils disparaissent en production car les settings sont conditionnels (`if not DEBUG`). Voir détail ci-dessous.

---

### Grille de contrôles

| # | Contrôle | Statut | Détail |
|---|---|---|---|
| 1 | **`DEBUG = False` en prod** | ✅ Conforme | Chargé via `config('DEBUG', default=False, cast=bool)` — `False` par défaut |
| 2 | **`SECRET_KEY` externalisée** | ✅ Conforme | `config('SECRET_KEY')` via python-decouple — non en dur |
| 3 | **`ALLOWED_HOSTS` restrictif** | ✅ Conforme | `['127.0.0.1', 'localhost', '51.210.240.185', 'bana.mobi', 'www.bana.mobi']` |
| 4 | **Credentials DB externalisés** | ✅ Conforme | `DB_NAME`, `DB_USER`, `DB_PASSWORD` via decouple |
| 5 | **`CsrfViewMiddleware` actif** | ✅ Conforme | Présent dans `MIDDLEWARE` |
| 6 | **`SESSION_COOKIE_SECURE`** | ✅ Conforme | `True` si `not DEBUG` (production) |
| 7 | **`CSRF_COOKIE_SECURE`** | ✅ Conforme | `True` si `not DEBUG` |
| 8 | **`SESSION_COOKIE_HTTPONLY`** | ✅ Conforme | Django default = True |
| 9 | **`SECURE_HSTS_SECONDS`** | ✅ Conforme | `31536000` (1 an) si `not DEBUG` |
| 10 | **`SECURE_HSTS_INCLUDE_SUBDOMAINS`** | ✅ Conforme | `True` si `not DEBUG` |
| 11 | **`SECURE_HSTS_PRELOAD`** | ✅ Conforme | `True` si `not DEBUG` |
| 12 | **`SECURE_PROXY_SSL_HEADER`** | ✅ Conforme | `('HTTP_X_FORWARDED_PROTO', 'https')` si `not DEBUG` |
| 13 | **`SECURE_BROWSER_XSS_FILTER`** | ✅ Conforme | `True` si `not DEBUG` |
| 14 | **`SECURE_CONTENT_TYPE_NOSNIFF`** | ✅ Conforme | `True` si `not DEBUG` |
| 15 | **`X_FRAME_OPTIONS`** | ✅ Conforme | `'DENY'` si `not DEBUG` |
| 16 | **`SECURE_SSL_REDIRECT`** | ⚠️ Non configuré | Non défini en Python — redirection HTTPS gérée par Nginx (acceptable si Nginx est bien configuré) |
| 17 | **Version Django** | ⚠️ Amélioration recommandée | Django `5.1.4` — version active mais **pas la LTS**. Django 5.2 LTS est disponible. |
| 18 | **`AUTH_PASSWORD_VALIDATORS`** | ✅ Conforme | 4 validateurs actifs dont longueur min 12 caractères |
| 19 | **Hashers** | ✅ Conforme | Django 5.x utilise PBKDF2/SHA-256 par défaut |
| 20 | **Middleware stack** | ✅ Conforme | `SecurityMiddleware` en premier, ordre correct |
| 21 | **Admin Django** | ⚠️ Amélioration recommandée | URL par défaut `/admin/` — non protégée par IP restriction |
| 22 | **Webhook Stripe** | ✅ Conforme | `@csrf_exempt` + `@require_POST` + vérification signature `stripe.Webhook.construct_event()` |
| 23 | **`ACCOUNT_PREVENT_ENUMERATION`** | ✅ Conforme | `True` — empêche l'énumération des emails |
| 24 | **`ACCOUNT_EMAIL_VERIFICATION`** | ✅ Conforme | `'mandatory'` |
| 25 | **`ACCOUNT_EMAIL_CONFIRMATION_HMAC`** | ✅ Conforme | `True` |
| 26 | **File upload validation** | ✅ Conforme | `ALLOWED_ATTACHMENT_TYPES` liste blanche MIME, `MAX_ATTACHMENT_SIZE = 5 MB` |
| 27 | **`FILE_UPLOAD_PERMISSIONS`** | ✅ Conforme | `0o664` |
| 28 | **CORS** | 🔴 Critique | `django-cors-headers` installé **mais non configuré** dans settings.py (aucune `CORS_*` setting). Status inconnu : soit CORS refusé par défaut (acceptable), soit autre middleware CORS actif. |
| 29 | **Logging** | ⚠️ Amélioration recommandée | Logs `bug_tracker` et `stripe_sub` actifs. Pas de log d'erreurs 500 centralisé. `site_visits.log` en chemin relatif (risque en prod) |
| 30 | **Cache** | ⚠️ Amélioration recommandée | `LocMemCache` — non persistant, non partagé entre workers Gunicorn. En production multi-worker, le cache n'est pas cohérent. Redis est déjà disponible (channels_redis) |

---

### Injections SQL
Résultat de la recherche (`grep -rn "raw(\|extra(\|RawSQL\|cursor.execute"`) :
**Aucune occurrence trouvée.** Toutes les requêtes utilisent l'ORM Django standard. ✅ Conforme

---

### XSS — Utilisation de `|safe` et `mark_safe`

| Emplacement | Usage | Risque |
|---|---|---|
| `bug_tracker/admin.py` | `from django.utils.safestring import mark_safe` | Importé mais usage à vérifier dans l'admin — contexte restreint (superuser uniquement) |
| `bana/templates/tarifs.html:99` | `{{ item.description\|safe }}` | ⚠️ La description vient d'un dict Python défini en dur dans la vue — pas de données utilisateur. Faible risque actuel, mais pratique à éviter. |
| `bana/templates/home.html:96` | `{{ benefit.description\|safe }}` | Idem — données statiques. Faible risque. |
| `bana/templates/work.html:179` | `{{ benefit.description\|safe }}` | Idem. |
| `bana/templates/work.html:246` | `{{ step.description\|safe }}` | Idem. |

**Conclusion :** Le `|safe` est utilisé sur des chaînes HTML codées **en dur dans les vues** (pas de données utilisateur). Le risque XSS est actuellement nul sur ces usages. Cependant, si ces textes deviennent éditables (CMS), cela deviendrait un risque critique. Recommandé : utiliser `format_html()` dans la vue plutôt que `|safe` dans le template.

---

### Contrôle d'accès
| Contrôle | Statut | Détail |
|---|---|---|
| Vues connectées | ✅ | `@login_required` systématique |
| Vues superuser | ✅ | `if not request.user.is_superuser: raise PermissionDenied` |
| Vue chat `/chat/chat/` | 🔴 | **Pas de `@login_required`** — n'importe qui peut accéder à la page chat |
| `redirect_after_email_confirmation` | ⚠️ | Non protégée — utilise `request.session.pop` (pas de fuite de données) |
| `payment_cancelled` | ⚠️ | Non protégée — acceptable pour une page d'annulation |
| `switch_language` | ✅ | Valide la langue ET l'URL referer avec `url_has_allowed_host_and_scheme()` |
| `add_child_view` | ✅ | Valide le paramètre `next` avec `url_has_allowed_host_and_scheme()` |

---

### Dépendances (extrait `pip freeze`)

| Package | Version | Note |
|---|---|---|
| Django | 5.1.4 | ⚠️ Pas la LTS (5.2). Mettre à jour. |
| stripe | 12.3.0 | ✅ Récente |
| django-allauth | 65.7.0 | ✅ Récente |
| cryptography | 44.0.0 | ✅ |
| Pillow | 11.2.1 | ✅ |
| channels | 4.2.2 | ✅ |
| daphne | 4.2.1 | ✅ |
| psycopg | 3.2.9 | ✅ Psycopg3 moderne |
| django-cors-headers | 4.6.0 | ⚠️ Installé mais non configuré |
| django-cors-middleware | 1.5.0 | ⚠️ Installé (doublon avec cors-headers ?) |
| numpy | 2.4.6 | ⚠️ Présent sans usage visible dans le code Django |
| django-ckeditor | 6.7.2 | ⚠️ Installé mais non listé dans `INSTALLED_APPS` |
| django-livesync | 0.5 | ⚠️ Package non maintenu, potentiellement inutile |

---

### Bug Fonctionnel Sécurité-Critique

| # | Description | Impact |
|---|---|---|
| BUG-01 | `stripe_sub/views.py` — `Profile.objects.get(stripe_customer_id=...)` : le champ `stripe_customer_id` **n'existe pas sur `Profile`**. Provoque une `FieldError` sur les événements `invoice.payment_succeeded`. | 🔴 Le renouvellement automatique des abonnements échoue silencieusement |
| BUG-02 | `_update_profile_customer_id()` : `profile.stripe_customer_id = customer_id` suivi de `profile.save()` — le champ n'existe pas, la valeur n'est jamais persistée. | 🔴 Le mapping customer Stripe → utilisateur est perdu après checkout |

---

## 4B — Sécurité Serveur (Debian 12 Dédié)

> **Note :** L'audit serveur nécessite un accès SSH direct au serveur de production. Les éléments ci-dessous sont évalués à partir des informations disponibles dans le code source et la configuration visible.

### Éléments évalués depuis le code

| Contrôle | Statut | Détail |
|---|---|---|
| **Gunicorn user** | ⚠️ À vérifier | Service systemd `bana-gunicorn` — vérifier que l'user n'est pas root |
| **Socket vs TCP** | ⚠️ À vérifier | `gunicorn_config.py` présent à la racine mais non listé dans les fichiers analysés |
| **Nginx headers sécurité** | ⚠️ À vérifier | Non visible depuis le code Python — à auditer dans `/etc/nginx/sites-enabled/` |
| **Accès `.env` via Nginx** | ⚠️ À vérifier | S'assurer que `/bana/.env` n'est pas accessible via Nginx |
| **Fail2ban SSH** | ⚠️ À vérifier | – |
| **PostgreSQL privileges** | ⚠️ À vérifier | L'utilisateur Django ne doit pas être superuser PostgreSQL |
| **SSL/TLS** | ⚠️ À vérifier | Certbot détecté dans les scripts — vérifier TLSv1.2+ uniquement, OCSP stapling |
| **Port 8001 (Daphne)** | ⚠️ À vérifier | Daphne tourne sur port 8001 — vérifier qu'il n'est pas exposé publiquement (doit être derrière Nginx) |
| **Redis** | ⚠️ À vérifier | Redis utilisé pour Django Channels — vérifier bind sur 127.0.0.1 uniquement |

### Commandes à exécuter sur le serveur

```bash
# Vérifier user gunicorn
ps aux | grep gunicorn

# Ports ouverts
ss -tlnp

# Configuration Nginx
nginx -t
cat /etc/nginx/sites-enabled/*

# PostgreSQL privileges
sudo -u postgres psql -c "SELECT rolname, rolsuper FROM pg_roles WHERE rolcanlogin = true;"

# SSH configuration
grep -E "^(PermitRootLogin|PasswordAuthentication)" /etc/ssh/sshd_config

# Fail2ban
fail2ban-client status

# Mises à jour en attente
apt list --upgradable 2>/dev/null | head -20

# Certificat SSL
certbot certificates

# Redis bind
grep "^bind" /etc/redis/redis.conf
```

---

## Résumé des Findings Sécurité

| # | Finding | Criticité | Action |
|---|---|---|---|
| S01 | Vue chat sans `@login_required` | 🔴 Critique | Ajouter `@login_required` |
| S02 | Bug `stripe_customer_id` manquant sur Profile | 🔴 Critique | Ajouter le champ et migrer, ou corriger la logique |
| S03 | `django-cors-headers` installé sans config | 🔴 Critique | Configurer `CORS_ALLOWED_ORIGINS` explicitement |
| S04 | URL admin `/admin/` par défaut | ⚠️ Modéré | Personnaliser l'URL admin |
| S05 | Django 5.1.4 (pas LTS) | ⚠️ Modéré | Migrer vers Django 5.2 LTS |
| S06 | `|safe` sur textes statiques | ⚠️ Faible | Remplacer par `format_html()` par précaution |
| S07 | Cache `LocMemCache` en multi-worker | ⚠️ Modéré | Passer à `django.core.cache.backends.redis.RedisCache` |
| S08 | Log `site_visits.log` en chemin relatif | ⚠️ Faible | Utiliser chemin absolu |
| S09 | `django-cors-middleware` doublon | ⚠️ Faible | Désinstaller l'un des deux |
| S10 | `numpy` présent sans usage visible | ⚠️ Faible | Vérifier et supprimer si inutile |
| S11 | Accès serveur Daphne port 8001 | ⚠️ À vérifier | S'assurer du blocage réseau |
| S12 | Redis non sécurisé | ⚠️ À vérifier | Vérifier bind 127.0.0.1 |
