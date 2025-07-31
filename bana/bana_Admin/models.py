from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

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

