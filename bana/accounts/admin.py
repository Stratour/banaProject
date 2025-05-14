from django.contrib import admin
from .models import Profile  # Import du modèle Profile

admin.site.register(Profile)  # Enregistrer le modèle dans l'admin
