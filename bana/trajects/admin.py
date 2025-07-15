from django.contrib import admin
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode


    
@admin.register(Traject)
class TrajectAdmin(admin.ModelAdmin):
    list_display = ('start_adress', 'start_street', 'end_adress', 'end_street', 'get_proposed_users', 'get_researched_users')
    search_fields = ('start_name', 'start_street', 'end_name', 'end_street')

    def get_proposed_users(self, obj):
        users = ProposedTraject.objects.filter(traject=obj).values_list('user__username', flat=True)
        return ", ".join(users)
    get_proposed_users.short_description = 'Proposed Users'

    def get_researched_users(self, obj):
        users = ResearchedTraject.objects.filter(traject=obj).values_list('user__username', flat=True)
        return ", ".join(users)
    get_researched_users.short_description = 'Researched Users'


@admin.register(ProposedTraject)
class ProposedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        'traject', 'details', 'get_user', 
        'departure_time', 'arrival_time', 'get_start_location', 
        'get_end_location', 'get_transport_modes','number_of_places', 'get_languages'
    )
    search_fields = ('traject__start_street', 'traject__end_street', 'traject__start_name','traject__end_name')

    def get_user(self, obj):
        return obj.user.username if obj.user else "—"
    get_user.short_description = 'User'

    def get_start_location(self, obj):
        return obj.traject.start_street
    get_start_location.short_description = 'Start Street'

    def get_end_location(self, obj):
        return obj.traject.end_street
    get_end_location.short_description = 'End Street'

    def get_transport_modes(self, obj):
        return ", ".join([mode.name for mode in obj.transport_modes.all()])
    get_transport_modes.short_description = 'Transport Modes'

    def get_languages(self, obj):
        return ", ".join(lang.lang_name for lang in obj.languages.all())
    get_languages.short_description = "Langues parlées"
    
    
@admin.register(ResearchedTraject)
class ResearchedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        'traject', 'details', 'get_user', 
        'departure_time', 'arrival_time', 'get_transport_modes','number_of_places', 'get_languages'
    )
    search_fields = ( 'traject__start_name','traject__end_name')

    def get_user(self, obj):
        return obj.user.username if obj.user else "—"
    get_user.short_description = 'User'

    def get_transport_modes(self, obj):
        return ", ".join([mode.name for mode in obj.transport_modes.all()])
    get_transport_modes.short_description = 'Transport Modes'
    
    def get_languages(self, obj):
        return ", ".join(lang.lang_name for lang in obj.languages.all())
    get_languages.short_description = "Langues parlées"


@admin.register(TransportMode)
class TransportModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
