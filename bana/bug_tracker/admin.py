from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Bug, BugComment, BugAttachment, BugHistory, Component, Version, Environment

@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'bug_count']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def bug_count(self, obj):
        return obj.bug_set.count()
    bug_count.short_description = 'Nombre de bugs'

@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['name', 'release_date', 'is_active', 'affected_bugs_count', 'fixed_bugs_count']
    list_filter = ['is_active', 'release_date']
    search_fields = ['name']
    ordering = ['-release_date']
    
    def affected_bugs_count(self, obj):
        return obj.affected_bugs.count()
    affected_bugs_count.short_description = 'Bugs affectés'
    
    def fixed_bugs_count(self, obj):
        return obj.fixed_bugs.count()
    fixed_bugs_count.short_description = 'Bugs corrigés'

@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'bug_count']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def bug_count(self, obj):
        return obj.bug_set.count()
    bug_count.short_description = 'Nombre de bugs'

class BugCommentInline(admin.TabularInline):
    model = BugComment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['author', 'content', 'created_at', 'updated_at']

class BugAttachmentInline(admin.TabularInline):
    model = BugAttachment
    extra = 0
    readonly_fields = ['uploaded_at']
    fields = ['file', 'filename', 'uploaded_by', 'uploaded_at']

class BugHistoryInline(admin.TabularInline):
    model = BugHistory
    extra = 0
    readonly_fields = ['timestamp']
    fields = ['user', 'field_changed', 'old_value', 'new_value', 'timestamp']
    ordering = ['-timestamp']

@admin.register(Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title_short', 'status_badge', 'priority_badge', 'severity_badge', 
        'component', 'assigned_to', 'reported_by', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'severity', 'component', 
        'affected_version', 'environment', 'created_at'
    ]
    search_fields = ['title', 'description', 'reproduction_steps']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'reproduction_steps')
        }),
        ('Classification', {
            'fields': ('status', 'priority', 'severity'),
            'classes': ['collapse']
        }),
        ('Type de bug', {
            'fields': ('component', 'affected_version', 'fixed_version')
        }),
        ('Assignation', {
            'fields': ('assigned_to', 'reported_by'),
        }),
        ('Environnement', {
            'fields': ('environment', 'operating_system', 'browser', 'device'),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    inlines = [BugCommentInline, BugAttachmentInline, BugHistoryInline]
    
    actions = ['mark_as_resolved', 'mark_as_closed', 'assign_to_me']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Titre'
    title_short.admin_order_field = 'title'
    
    def status_badge(self, obj):
        colors = {
            'open': '#0dcaf0',
            'in_progress': '#ffc107',
            'resolved': '#198754',
            'closed': '#6c757d',
            'reopened': '#dc3545',
            'duplicate': '#6c757d',
            'wont_fix': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#198754',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priorité'
    priority_badge.admin_order_field = 'priority'
    
    def severity_badge(self, obj):
        colors = {
            'minor': '#d1ecf1',
            'normal': '#d4edda',
            'major': '#fff3cd',
            'critical': '#f8d7da',
            'blocker': '#f5c6cb'
        }
        bg_color = colors.get(obj.severity, '#e2e3e5')
        return format_html(
            '<span style="background-color: {}; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            bg_color,
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Sévérité'
    severity_badge.admin_order_field = 'severity'
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} bug(s) marqué(s) comme résolu(s).')
    mark_as_resolved.short_description = "Marquer comme résolu"
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} bug(s) fermé(s).')
    mark_as_closed.short_description = "Fermer"
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} bug(s) assigné(s) à vous.')
    assign_to_me.short_description = "M'assigner"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'component', 'assigned_to', 'reported_by', 'affected_version', 'environment'
        )

@admin.register(BugComment)
class BugCommentAdmin(admin.ModelAdmin):
    list_display = ['bug_link', 'author', 'content_short', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'bug__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def bug_link(self, obj):
        url = reverse('admin:bug_tracker_bug_change', args=[obj.bug.pk])
        return format_html('<a href="{}">{}</a>', url, obj.bug)
    bug_link.short_description = 'Bug'
    bug_link.admin_order_field = 'bug'
    
    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = 'Contenu'

@admin.register(BugAttachment)
class BugAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'bug_link', 'uploaded_by', 'uploaded_at', 'file_size']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['filename', 'bug__title']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def bug_link(self, obj):
        url = reverse('admin:bug_tracker_bug_change', args=[obj.bug.pk])
        return format_html('<a href="{}">{}</a>', url, obj.bug)
    bug_link.short_description = 'Bug'
    bug_link.admin_order_field = 'bug'
    
    def file_size(self, obj):
        try:
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except:
            return "Inconnu"
    file_size.short_description = 'Taille'

@admin.register(BugHistory)
class BugHistoryAdmin(admin.ModelAdmin):
    list_display = ['bug_link', 'user', 'field_changed', 'old_value_short', 'new_value_short', 'timestamp']
    list_filter = ['field_changed', 'timestamp', 'user']
    search_fields = ['bug__title', 'old_value', 'new_value']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def bug_link(self, obj):
        url = reverse('admin:bug_tracker_bug_change', args=[obj.bug.pk])
        return format_html('<a href="{}">{}</a>', url, obj.bug)
    bug_link.short_description = 'Bug'
    bug_link.admin_order_field = 'bug'
    
    def old_value_short(self, obj):
        return obj.old_value[:50] + '...' if len(obj.old_value) > 50 else obj.old_value
    old_value_short.short_description = 'Ancienne valeur'
    
    def new_value_short(self, obj):
        return obj.new_value[:50] + '...' if len(obj.new_value) > 50 else obj.new_value
    new_value_short.short_description = 'Nouvelle valeur'

# Configuration du site admin
admin.site.site_header = "Bug Tracker Administration"
admin.site.site_title = "Bug Tracker Admin"
admin.site.index_title = "Gestion des Bugs"
