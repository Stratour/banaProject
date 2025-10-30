from django.contrib import admin
from .models import (
    Traject,
    ProposedTraject,
    ResearchedTraject,
    TransportMode,
    Reservation,
)
from django.utils.translation import gettext_lazy as _


# ============================================================
# 🌍 TRAJECT
# ============================================================
@admin.register(Traject)
class TrajectAdmin(admin.ModelAdmin):
    list_display = ("id", "start_adress", "end_adress", "get_coordinates")
    search_fields = ("start_adress", "end_adress")
    list_per_page = 25

    def get_coordinates(self, obj):
        """Affiche les coordonnées du point de départ (si disponibles)."""
        if obj.start_point:
            return f"{obj.start_point.y:.5f}, {obj.start_point.x:.5f}"
        return "—"
    get_coordinates.short_description = "Coordonnées départ"


# ============================================================
# 🚗 PROPOSED TRAJECT
# ============================================================
@admin.register(ProposedTraject)
class ProposedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "get_start_adress", "get_end_adress",
        "date", "departure_time", "arrival_time",
        "is_simple", "search_radius_km", "is_active"
    )
    list_filter = ("is_active", "is_simple", "date")
    search_fields = (
        "user__username",
        "traject__start_adress",
        "traject__end_adress",
    )
    list_per_page = 25
    ordering = ("-date", "departure_time")

    @admin.display(description="Adresse départ")
    def get_start_adress(self, obj):
        return obj.traject.start_adress if obj.traject else "—"

    @admin.display(description="Adresse arrivée")
    def get_end_adress(self, obj):
        return obj.traject.end_adress if obj.traject else "—"


# ============================================================
# 🔍 RESEARCHED TRAJECT
# ============================================================
@admin.register(ResearchedTraject)
class ResearchedTrajectAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "get_start_adress", "get_end_adress",
        "date", "departure_time", "arrival_time", "is_active"
    )
    list_filter = ("is_active", "date")
    search_fields = (
        "user__username",
        "traject__start_adress",
        "traject__end_adress",
    )
    list_per_page = 25
    ordering = ("-date", "departure_time")

    @admin.display(description="Adresse départ")
    def get_start_adress(self, obj):
        return obj.traject.start_adress if obj.traject else "—"

    @admin.display(description="Adresse arrivée")
    def get_end_adress(self, obj):
        return obj.traject.end_adress if obj.traject else "—"


# ============================================================
# 🚌 TRANSPORT MODE
# ============================================================
@admin.register(TransportMode)
class TransportModeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


# ============================================================
# 📅 RESERVATION
# ============================================================
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "get_start_adress", "get_end_adress",
        "number_of_places", "status", "reservation_date"
    )
    list_filter = ("status", "reservation_date")
    search_fields = (
        "user__username",
        "traject__traject__start_adress",
        "traject__traject__end_adress",
    )
    ordering = ("-reservation_date",)
    list_per_page = 25

    @admin.display(description="Adresse départ")
    def get_start_adress(self, obj):
        return getattr(obj.traject.traject, "start_adress", "—")

    @admin.display(description="Adresse arrivée")
    def get_end_adress(self, obj):
        return getattr(obj.traject.traject, "end_adress", "—")
