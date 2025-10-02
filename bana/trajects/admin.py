from django.contrib import admin
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation


    
@admin.register(Traject)
class TrajectAdmin(admin.ModelAdmin): 
    list_display = ("id", "start_adress", "end_adress", "start_point", "end_point")
    search_fields = ("start_adress", "end_adress")


@admin.register(ProposedTraject)
class ProposedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "get_start_adress", "get_end_adress",
        "departure_time", "arrival_time", "date", "is_active"
    )
    list_filter = ("is_active", "date")
    search_fields = ("user__username", "traject__start_adress", "traject__end_adress")

    def get_start_adress(self, obj):
        return obj.traject.start_adress if obj.traject else "-"
    get_start_adress.short_description = "Adresse départ"

    def get_end_adress(self, obj):
        return obj.traject.end_adress if obj.traject else "-"
    get_end_adress.short_description = "Adresse arrivée"
    
    
@admin.register(ResearchedTraject)
class ResearchedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "get_start_adress", "get_end_adress",
        "departure_time", "arrival_time", "date", "is_active"
    )
    list_filter = ("is_active", "date")
    search_fields = ("user__username", "traject__start_adress", "traject__end_adress")

    def get_start_adress(self, obj):
        return obj.traject.start_adress if obj.traject else "-"
    get_start_adress.short_description = "Adresse départ"

    def get_end_adress(self, obj):
        return obj.traject.end_adress if obj.traject else "-"
    get_end_adress.short_description = "Adresse arrivée"



@admin.register(TransportMode)
class TransportModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    
#@admin.register(Reservation)
#class ReservationAdmin(admin.ModelAdmin):
#    list_display = ('id', 'user', 'traject', 'number_of_places', 'status', 'reservation_date')
#    list_filter = ('status', 'reservation_date')
#    search_fields = ('user__username', 'traject__traject__start_adress', 'traject__traject__end_adress')
#    ordering = ('-reservation_date',)
