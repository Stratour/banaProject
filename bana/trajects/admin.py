from django.contrib import admin
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode

@admin.register(Traject)
class TrajectAdmin(admin.ModelAdmin):
    list_display = ('start_name','start_street','end_name','end_street', 'get_proposed_members', 'get_researched_members')
    search_fields = ('start_name','start_street','end_name', 'end_street')

    def get_proposed_members(self, obj):
        members = ProposedTraject.objects.filter(traject=obj).values_list('member__memb_user_fk__username', flat=True)
        return ", ".join(members)
    get_proposed_members.short_description = 'Proposed Members'

    def get_researched_members(self, obj):
        members = ResearchedTraject.objects.filter(traject=obj).values_list('member__memb_user_fk__username', flat=True)
        return ", ".join(members)
    get_researched_members.short_description = 'Researched Members'


@admin.register(ProposedTraject)
class ProposedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        'traject', 'details', 'get_members', 
        'departure_time', 'arrival_time', 'get_start_location', 
        'get_end_location', 'get_transport_modes', 'language','number_of_places'
    )
    search_fields = ('traject__start_street', 'traject__end_street', 'traject__start_name','traject__end_name')

    def get_members(self, obj):
        return ", ".join([member.memb_user_fk.username for member in obj.member.all()])
    get_members.short_description = 'Members'

    def get_start_location(self, obj):
        return obj.traject.start_street
    get_start_location.short_description = 'Start Street'

    def get_end_location(self, obj):
        return obj.traject.end_street
    get_end_location.short_description = 'End Street'

    def get_transport_modes(self, obj):
        return ", ".join([mode.name for mode in obj.transport_modes.all()])
    get_transport_modes.short_description = 'Transport Modes'


@admin.register(ResearchedTraject)
class ResearchedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        'traject', 'details', 'get_members', 
        'departure_time', 'arrival_time', 'get_start_location', 
        'get_end_location', 'get_transport_modes','language','number_of_places'
    )
    search_fields = ('traject__start_street', 'traject__end_street', 'traject__start_name','traject__end_name')

    def get_members(self, obj):
        return ", ".join([member.memb_user_fk.username for member in obj.member.all()])
    get_members.short_description = 'Members'

    def get_start_location(self, obj):
        return obj.traject.start_street
    get_start_location.short_description = 'Start Street'

    def get_end_location(self, obj):
        return obj.traject.end_street
    get_end_location.short_description = 'End Street'

    def get_transport_modes(self, obj):
        return ", ".join([mode.name for mode in obj.transport_modes.all()])
    get_transport_modes.short_description = 'Transport Modes'


@admin.register(TransportMode)
class TransportModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
