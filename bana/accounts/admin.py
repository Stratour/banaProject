from django.contrib import admin
from .models import Profile, Languages  # Import du modèle Profile

admin.site.register(Profile)  # Enregistrer le modèle dans l'admin
admin.site.register(Languages)  # Enregistrer le modèle dans l'admin
