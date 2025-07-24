from django.contrib import admin
from .models import Profile, Languages, Child  # Import du modèle Profile

admin.site.register(Profile)  # Enregistrer le modèle dans l'admin
admin.site.register(Languages)  # Enregistrer le modèle dans l'admin

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    """
    Personnalisation de l'affichage du modèle Child dans l'interface d'administration.
    """
    
    # Affiche ces champs dans la liste des enfants
    list_display = (
        'chld_surname', 
        'chld_name', 
        'chld_gender', 
        'chld_birthdate', 
        'chld_user',  # Affiche l'utilisateur parent
        'chld_seat'
    )
    
    # Ajoute une barre de filtres sur le côté
    list_filter = (
        'chld_gender', 
        'chld_seat', 
        'chld_user'
    )
    
    # Ajoute une barre de recherche
    search_fields = (
        'chld_name', 
        'chld_surname', 
        'chld_user__username', # Permet de chercher par le nom d'utilisateur du parent
        'chld_user__email'
    )
    
    # Organise les champs dans le formulaire de modification/création
    fieldsets = (
        ('Informations sur l\'enfant', {
            'fields': ('chld_name', 'chld_surname', 'chld_gender', 'chld_birthdate')
        }),
        ('Informations parentales et autres', {
            'fields': ('chld_user', 'chld_seat', 'chld_spcl_attention')
        }),
    )

    # Améliore la sélection pour la ForeignKey vers User
    raw_id_fields = ('chld_user',)
