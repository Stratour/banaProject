from django.contrib import admin
from .models import Profile, Languages, Child  # Import du modèle Profile

admin.site.register(Profile)  # Enregistrer le modèle dans l'admin
class ProfileAdmin(admin.ModelAdmin):
    # Champs affichés dans la liste des profils
    list_display = (
        'user',
        'service',
        'ci_is_verified',
        'bvm_is_verified',
        'prfl_is_verified',
        'address',
    )
    # Filtres disponibles sur le côté droit
    list_filter = (
        'service',
        'ci_is_verified',
        'bvm_is_verified',
        'prfl_is_verified',
    )
    # Champs sur lesquels la barre de recherche peut opérer
    search_fields = (
        'user__username', # Permet de rechercher par le nom d'utilisateur associé
        'user__first_name',
        'user__last_name',
        'address',
        'bio',
        'verified_first_name',
        'verified_last_name',
    )
    # Utilisation de raw_id_fields pour une meilleure performance avec beaucoup d'utilisateurs
    raw_id_fields = ('user',)
    # Organisation des champs dans le formulaire d'édition
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'service', 'bio', 'address')
        }),
        ('Statut de Vérification', {
            'fields': ('ci_is_verified', 'bvm_is_verified', 'prfl_is_verified', 'document_bvm')
        }),
        ('Vérification Stripe Identity', {
            'fields': (
                'verified_first_name',
                'verified_last_name',
                'verified_address',
                'verified_dob',
                'document_image_url'
            ),
            'classes': ('collapse',) # Rend cette section pliable
        }),
        ('Préférences & Autres', {
            'fields': ('languages', 'transport_modes')
        }),
    )
    # Améliore le widget pour les champs ManyToMany
    filter_horizontal = ('languages',)

admin.site.register(Languages)  # Enregistrer le modèle dans l'admin
class LanguagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Affiche l'ID et le nom dans la liste
    ordering = ('name',)  # Définit le tri par défaut par nom alphabétique



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
