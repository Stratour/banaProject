
# Create your views here.
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import InscriptionValidation, SiteVisit
from django.contrib.auth.models import User
from accounts.models import Profile
from datetime import timedelta
from django.db.models import Count, Prefetch, Q
from django.core.paginator import Paginator
from stripe_sub.models import Subscription


MEMBER_SORT_OPTIONS = [
    ('-user__date_joined', "Inscription (plus récente d'abord)"),
    ('user__date_joined', "Inscription (plus ancienne d'abord)"),
    ('user__email', 'Email (A → Z)'),
    ('-user__email', 'Email (Z → A)'),
    ('verified_last_name', 'Nom (A → Z)'),
    ('-verified_last_name', 'Nom (Z → A)'),
    ('service', 'Rôle (A → Z)'),
    ('-ci_is_verified', 'CI vérifiée en premier'),
    ('-bvm_is_verified', 'BVM vérifié en premier'),
    ('-prfl_is_verified', 'Profil vérifié en premier'),
]
MEMBER_SORT_VALID_FIELDS = {value for value, _label in MEMBER_SORT_OPTIONS}

MEMBER_FILTER_OPTIONS = [
    ('all', 'Tous'),
    ('yaya', 'Yaya'),
    ('parent', 'Parent'),
    ('bvm_pending', 'BVM en attente'),
]
MEMBER_FILTER_VALID_VALUES = {value for value, _label in MEMBER_FILTER_OPTIONS}


@login_required
def admin_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    context = {}
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})
    return render(request, 'bana_admin/admin_view.html', context)


@login_required
def site_stats_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    now = timezone.now()
    period = request.GET.get("period", "global")

    period_map = {"day": 1, "week": 7, "month": 30}
    days = period_map.get(period)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    period_start = now - timedelta(days=days) if days else None
    if period == "year":
        period_start = year_start

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago   = now - timedelta(days=7)
    month_ago  = now - timedelta(days=30)

    # KPIs fixes (indépendants de la période)
    kpis = {
        "total_members":    User.objects.count(),
        "new_today":        User.objects.filter(date_joined__gte=today_start).count(),
        "new_week":         User.objects.filter(date_joined__gte=week_ago).count(),
        "new_month":        User.objects.filter(date_joined__gte=month_ago).count(),
        "active_today":     SiteVisit.objects.filter(last_seen__gte=today_start).count(),
        "active_week":      SiteVisit.objects.filter(last_seen__gte=week_ago).count(),
    }

    # Nouveaux inscrits selon période (pour la carte)
    if period == "day":
        new_members = kpis["new_today"]
    elif period == "week":
        new_members = kpis["new_week"]
    elif period == "month":
        new_members = kpis["new_month"]
    elif period == "year":
        new_members = User.objects.filter(date_joined__gte=year_start).count()
    else:
        new_members = kpis["total_members"]

    # Membres actifs récemment, paginé
    active_members = SiteVisit.objects.select_related('user')
    if period_start:
        active_members = active_members.filter(last_seen__gte=period_start)
    active_members = active_members.order_by('-last_seen')
    paginator = Paginator(active_members, 10)
    visits = paginator.get_page(request.GET.get("page"))

    context = {
        "period": period,
        "period_choices": [
            ("global", "Global"),
            ("day",    "Aujourd'hui"),
            ("week",   "Cette semaine"),
            ("month",  "Ce mois"),
            ("year",   "Cette année"),
        ],
        "new_members":          new_members,
        "kpis":                 kpis,
        "visits":               visits,
    }
    return render(request, "bana_admin/site_stats.html", context)


@login_required
def validate_members(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    sort = request.GET.get('sort', '-user__date_joined')
    if sort not in MEMBER_SORT_VALID_FIELDS:
        sort = '-user__date_joined'

    member_filter = request.GET.get('filter', 'all')
    if member_filter not in MEMBER_FILTER_VALID_VALUES:
        member_filter = 'all'

    query = request.GET.get('q', '').strip()

    profiles = (
        Profile.objects
        .select_related('user')
        .prefetch_related(
            'languages',
            Prefetch(
                'user__subscription_set',
                queryset=Subscription.objects.order_by('-created_at'),
                to_attr='subscriptions_list',
            ),
        )
    )

    if member_filter == 'yaya':
        profiles = profiles.filter(service='Yaya')
    elif member_filter == 'parent':
        profiles = profiles.filter(service='Parent')
    elif member_filter == 'bvm_pending':
        profiles = profiles.filter(bvm_is_verified=False).exclude(document_bvm__in=['', None])

    if query:
        profiles = profiles.filter(
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(verified_first_name__icontains=query) |
            Q(verified_last_name__icontains=query)
        )

    profiles = profiles.order_by(sort)

    context = {
        'profiles': profiles,
        'sort': sort,
        'sort_options': MEMBER_SORT_OPTIONS,
        'member_filter': member_filter,
        'filter_options': MEMBER_FILTER_OPTIONS,
        'query': query,
    }
    if request.htmx:
        return render(request, 'bana_admin/partials/members_panel.html', context)
    return render(request, 'bana_admin/validate_members.html', context)

@login_required
def verify_bvm_prfl(request, profile_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        profile = get_object_or_404(Profile, id=profile_id)

        if not profile.bvm_is_verified:
            profile.bvm_is_verified = True
            profile.save()
            profile.update_profile_verified()
            messages.success(request, f'Le statut BVM pour {profile.user.username} a été validé avec succès.')
        else:
            messages.warning(request, f'Le profil de {profile.user.username} avait déjà un BVM validé.')

        return redirect('bana_admin:validate_members')

    messages.error(request, 'Méthode de requête non autorisée.')
    return redirect('admin_panel')


@login_required
def reject_bvm_prfl(request, profile_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        profile = get_object_or_404(Profile, id=profile_id)

        if profile.document_bvm:
            profile.document_bvm.delete(save=False)
            profile.bvm_is_verified = False
            profile.save(update_fields=['document_bvm', 'bvm_is_verified'])
            profile.update_profile_verified()
            messages.warning(request, f'Le document BVM de {profile.user.username} a été refusé et supprimé. L\'utilisateur devra en soumettre un nouveau.')
        else:
            messages.warning(request, f'{profile.user.username} n\'a pas de document BVM à refuser.')

        return redirect('bana_admin:validate_members')

    messages.error(request, 'Méthode de requête non autorisée.')
    return redirect('bana_admin:validate_members')


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin pour s'assurer que l'utilisateur est connecté et est un super-utilisateur.
    """
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission() # Redirige vers la page de connexion
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect(reverse_lazy('admin:index')) # Redirige vers l'admin ou une autre page

class ValidationListView(SuperuserRequiredMixin, ListView):
    model = InscriptionValidation
    template_name = 'validations/validation_list.html'
    context_object_name = 'validation_requests'
    ordering = ['-created_at'] # Tri par date de création décroissante

class ValidateUserView(SuperuserRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        validation_request = get_object_or_404(InscriptionValidation, pk=pk)
        validation_request.is_validated = True
        validation_request.validation_date = timezone.now()
        validation_request.save()
        # Vous pouvez également activer l'utilisateur associé ici si nécessaire
        # validation_request.user.is_active = True
        # validation_request.user.save()
        messages.success(request, f"La demande pour {validation_request.user.username} a été validée.")
        return redirect(reverse_lazy('validations:list'))

class RejectUserView(SuperuserRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        validation_request = get_object_or_404(InscriptionValidation, pk=pk)
        validation_request.is_validated = False
        validation_request.validation_date = None # Ou une autre logique pour le rejet
        validation_request.save()
        messages.warning(request, f"La demande pour {validation_request.user.username} a été rejetée.")
        return redirect(reverse_lazy('validations:list'))


