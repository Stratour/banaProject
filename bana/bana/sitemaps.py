from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    i18n = True

    priorities = {
        "home": 1.0,
        "work": 0.9,
        "tarifs": 0.9,
        "parent": 0.8,
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
