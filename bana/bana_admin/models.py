from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class InscriptionValidation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='validation_request')
    is_validated = models.BooleanField(default=False)
    validation_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Validation pour {self.user.username} - Validé: {self.is_validated}"

    class Meta:
        verbose_name = "Demande de Validation d'Inscription"
        verbose_name_plural = "Demandes de Validation d'Inscriptions"


class SiteVisit(models.Model):
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now=True)  # dernière visite
    user_agent = models.CharField(max_length=512, blank=True, default='')

    class Meta:
        unique_together = ('ip_address', 'user')
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonyme"
        return f"{user_str} @ {self.ip_address} - Dernière visite : {self.timestamp}"
