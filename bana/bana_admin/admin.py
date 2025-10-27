from django.contrib import admin
from django.utils import timezone
from .models import InscriptionValidation, SiteVisit
from .utils import get_site_stats

@admin.register(InscriptionValidation)
class InscriptionValidationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_validated', 'validation_date', 'created_at')
    list_filter = ('is_validated',)
    search_fields = ('user__username', 'notes')
    actions = ['mark_as_validated', 'mark_as_pending']

    def mark_as_validated(self, request, queryset):
        queryset.update(is_validated=True, validation_date=timezone.now())
        self.message_user(request, "Les demandes sélectionnées ont été marquées comme validées.")
    mark_as_validated.short_description = "Marquer comme validé"

    def mark_as_pending(self, request, queryset):
        queryset.update(is_validated=False, validation_date=None)
        self.message_user(request, "Les demandes sélectionnées ont été marquées comme en attente.")
    mark_as_pending.short_description = "Marquer comme en attente"


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'ip_address', 'user')
    list_filter = ('timestamp', 'user')
    ordering = ('-timestamp',)

    #change_list_template = "admin/site_visit_changelist.html"

    #def changelist_view(self, request, extra_context=None):
    #    stats = get_site_stats()
    #    extra_context = extra_context or {}
    #    extra_context['stats'] = stats
    #    return super().changelist_view(request, extra_context=extra_context)