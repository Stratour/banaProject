# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BanaCommunity is a Django 5.1.4 community platform for ridesharing and childcare coordination. It uses PostGIS for geolocation-based matching, Django Channels for real-time chat, and Stripe for payments/identity verification.

## Commands

Always activate the project virtualenv before running any Python or `manage.py` command.

All `manage.py` commands must be run from the `bana/` directory (where `manage.py` lives):

```bash
cd bana/

# Development server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Translations (after editing .po files)
python manage.py compilemessages

# Disable past trajectories (scheduled task)
python manage.py disable_past_trajects

# Static files
python manage.py collectstatic
```

**Tailwind CSS** — run from project root while running the dev server:
```bash
python manage.py tailwind start
```
If Tailwind node modules are missing:
```bash
cd bana/theme/static_src && npm install && npm install cross-env && cd ../../..
```

**Production servers:**
```bash
gunicorn -c gunicorn_config.py bana.wsgi:application        # WSGI (port 9768)
daphne -b 0.0.0.0 -p 8001 bana.asgi:application             # ASGI for WebSocket
```

There is no configured test runner or linter in this project.

## Architecture

### App Structure

The Django project root is `bana/bana/` (settings, urls, wsgi, asgi). Custom apps live at `bana/<app>/`:

| App | Responsibility |
|---|---|
| `accounts` | User profiles, verification (CI/BVM), reviews, favorite addresses (GIS), Stripe Identity |
| `trajects` | Core ridesharing — routes, transport modes, carpool offers/requests with GIS radius matching |
| `chat` | Real-time messaging via Django Channels (WebSocket) |
| `stripe_sub` | Stripe payment processing and subscription webhooks |
| `bug_tracker` | In-app bug/issue reporting with file attachments |
| `bana_admin` | Admin dashboard, site visit stats (`SiteVisitMiddleware`), member validation |
| `members_back` | Member profile views and review system |
| `theme` | Tailwind CSS — source in `theme/static_src/`, compiled to `theme/static/` |

### Key Models

- **`accounts.Profile`** — extends `User` with verification flags (`is_ci_verified`, `is_bvm_verified`, `is_profile_verified`), transport mode preferences, languages, and a PostGIS `PointField` for location.
- **`trajects.Traject`** — a named route from source to destination (addresses + PostGIS coordinates).
- **`trajects.ProposedTraject`** — carpool offer linking a `Traject` to a user, with departure time, `number_of_places` (decremented on reservation confirmation), search radius (default 5km), recurrence pattern. `is_simple=True` means radius-only matching (Yaya sans destination fixe).
- **`trajects.ResearchedTraject`** — parent's childcare request, links a `Traject` to children and transport modes. Matched against `ProposedTraject` objects.
- **`trajects.Reservation`** — pending/confirmed/canceled booking between a `ResearchedTraject` and a `ProposedTraject`.
- **`accounts.FavoriteAddress`** — saved addresses with PostGIS `PointField`.

### Trajects — matching system

`trajects/views.py` contains the matching engine. Three source types:

| Type | Model | Matches against |
|---|---|---|
| `parent_research` | `ResearchedTraject` | `ProposedTraject` (all types) |
| `yaya_proposed` / `parent_proposed` | `ProposedTraject` (`is_simple=False`) | `ResearchedTraject` |
| `yaya_simple` | `ProposedTraject` (`is_simple=True`) | `ResearchedTraject` (start point only, no end point check) |

Entry point: `find_matching_trajects(obj)`. Uses PostGIS `Distance` with a 50km broad pre-filter, then fine Python filters (radius, transport mode, time window ±45min, seats).

### Templates — structure

Templates for the `trajects` app live in `bana/trajects/templates/trajects/` organized by feature:

```
partials/          — tab components (include via absolute path)
proposition/       — ProposedTraject (is_simple=False) views
proposition_rayon/ — ProposedTraject (is_simple=True) views
recherche/         — ResearchedTraject views
reservation/       — Reservation views
```

Each subdirectory contains: `creer.html`, `trajets_liste.html`, `trajet_detail.html`, `matchings.html`, `matching_detail.html` (where applicable). Always use absolute template paths in `render()` and `{% include %}`.

### GIS / Geolocation

The database backend is `django.contrib.gis.db.backends.postgis`. Any model with spatial queries uses `django.contrib.gis.db.models` (e.g., `PointField`, `Distance`). Geocoding is done via `geopy`.

### Real-time (Channels)

Django Channels is configured with `ASGI_APPLICATION = 'bana.asgi.application'`. The `chat` app handles WebSocket consumers. Daphne serves the ASGI app in production.

### Internationalization

Default language is French (`fr-fr`). Supported: `fr`, `en`, `nl`. Translation strings use `gettext_lazy` (`_(...)`). `.po` files are in each app's `locale/` directory. Always run `compilemessages` after editing translations.

### Authentication

Uses `django-allauth` with email-only login (`ACCOUNT_LOGIN_METHODS = {"email"}`). Email verification is mandatory. Google OAuth is configured. Custom signup form is at `accounts.forms.CustomSignupForm`.

### Environment Variables

Loaded via `python-decouple` from `bana/.env`. Required keys:
- `EMAIL_MDP` — OVH SMTP password
- `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_IDENTITY_FLUX`
- `OPEN_STREET_MAP_API`, `GOOGLE_MAPS_API_KEY`

The database credentials are currently hardcoded in `settings.py` (not from `.env`).

### Static / Media

- Tailwind compiled CSS: `bana/theme/static/`
- Collected static: `bana/staticfiles/` (after `collectstatic`)
- User uploads: `bana/media/`
