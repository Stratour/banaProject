import os
from datetime import datetime, timezone
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_FILES = {
    "home": "home.html",
    "work": "work.html",
    "tarifs": "tarifs.html",
    "yaya": "yaya.html",
    "about": "about.html",
    "contact": "contact.html",
}


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    i18n = True

    priorities = {
        "home": 1.0,
        "work": 0.9,
        "tarifs": 0.9,
        "yaya": 0.8,
        "about": 0.7,
        "contact": 0.6,
    }

    def items(self):
        return list(self.priorities.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.priorities.get(item, 0.5)

    def lastmod(self, item):
        path = os.path.join(TEMPLATES_DIR, TEMPLATE_FILES[item])
        return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
