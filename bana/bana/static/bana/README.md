# Structure des assets statiques — `bana/static/bana/`

## Règle générale

| Critère | Destination |
|---|---|
| Utilisé sur **≥ 2 pages** | `js/components/` ou `js/core/` / `css/components/` |
| Utilisé sur **1 seule page** | `js/pages/<page>.js` / `css/pages/<page>.css` |
| Librairie tierce (non modifiée) | `js/vendor/` |
| Service Worker | `js/sw.js` — **ne pas déplacer** (servi via une vue Django à `/sw.js`) |

---

## JavaScript — `js/`

```
js/
├── vendor/               # librairies tierces, jamais modifiées
│   └── htmx.min.js
│
├── core/                 # utilitaires partagés, chargés sur toutes les pages
│   ├── modal.js
│   ├── toast.js
│   └── address_autocomplete.js
│
├── components/           # composants UI réutilisables (≥ 2 pages)
│   ├── animate.js
│   ├── carousel.js
│   ├── slide.js
│   └── video.js
│
├── layout/               # scripts liés à la mise en page globale
│   └── header.js         # ex top-mobile-menu.js
│
├── pages/                # scripts propres à une seule page
│   └── faq.js            # utilisé sur tarifs.html et work.html
│
└── sw.js                 # Service Worker — scope racine, ne pas déplacer
```

### Chargement dans les templates

`vendor/`, `core/` et `layout/` sont chargés dans les `base.html`.  
Les fichiers `pages/` sont chargés dans le template de la page concernée via le bloc `{% block extra_js %}`.

```django
{# dans une page spécifique #}
{% block extra_js %}
  <script src="{% static 'bana/js/pages/faq.js' %}"></script>
{% endblock %}
```

---

## CSS — `css/`

```
css/
├── components/           # styles de composants réutilisables
│   ├── animate.css
│   ├── footer.css
│   └── toast.css
│
└── pages/                # styles propres à une seule page
    └── home.css          # utilisé sur home.html et about.html
```

Tailwind est géré séparément dans `theme/` — ne pas dupliquer ici.  
Chargement via `{% block extra_head %}` pour les CSS de page.

---

## Images — `img/`

```
img/
├── logo/                 # logos Bana et partenaires
├── icon/                 # icônes UI (SVG) + icônes PWA (PNG) + favicon
├── background/           # images de fond globales
├── shared/               # assets partagés sans page attribuée (logos sociaux, avatars par défaut…)
├── other/                # illustrations et photos génériques non attribuées à une page
└── pages/                # images liées à une page précise
    ├── home/
    ├── about/
    ├── contact/
    ├── parent/
    ├── tarifs/
    ├── work/
    └── yaya/
```

---

## Autres

```
video/                    # vidéos statiques (how_it_works.mp4…)
```

---

## Ajouter un nouvel asset

1. Identifier la catégorie (vendor / core / component / page-specific)
2. Placer dans le bon sous-dossier
3. Référencer via `{% static 'bana/<chemin>' %}` dans le template
4. Si CSS ou JS de page : utiliser `{% block extra_head %}` / `{% block extra_js %}`
5. Après tout changement en production : `python manage.py collectstatic`
