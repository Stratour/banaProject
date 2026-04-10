
# Create your views here.
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import InscriptionValidation, SiteVisit
from django.contrib.auth.models import User
from accounts.models import Profile
from datetime import timedelta
from django.db.models import Count
from django.core.paginator import Paginator
from .utils import get_site_stats


def admin_view(request):
    context = {}
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})
    return render(request, 'bana_admin/admin_view.html', context)


def site_stats_view(request):
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

    # Visites filtrées par période
    anon_qs = SiteVisit.objects.filter(user__isnull=True)
    auth_qs = SiteVisit.objects.filter(user__isnull=False).select_related('user')
    if period_start:
        anon_qs = anon_qs.filter(timestamp__gte=period_start)
        auth_qs = auth_qs.filter(timestamp__gte=period_start)

    anonymous_visits    = anon_qs.count()
    authenticated_visits = auth_qs.count()
    total_visits        = anonymous_visits + authenticated_visits

    # KPIs fixes (indépendants de la période)
    kpis = {
        "total_members":    User.objects.count(),
        "new_today":        User.objects.filter(date_joined__gte=today_start).count(),
        "new_week":         User.objects.filter(date_joined__gte=week_ago).count(),
        "new_month":        User.objects.filter(date_joined__gte=month_ago).count(),
        "active_today":     SiteVisit.objects.filter(user__isnull=False, timestamp__gte=today_start).count(),
        "active_week":      SiteVisit.objects.filter(user__isnull=False, timestamp__gte=week_ago).count(),
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

    # Table des visites paginée
    all_visits = SiteVisit.objects.select_related('user')
    if period_start:
        all_visits = all_visits.filter(timestamp__gte=period_start)
    all_visits = all_visits.order_by('-timestamp')
    paginator = Paginator(all_visits, 10)
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
        "anonymous_visits":     anonymous_visits,
        "authenticated_visits": authenticated_visits,
        "total_visits":         total_visits,
        "new_members":          new_members,
        "kpis":                 kpis,
        "visits":               visits,
    }
    return render(request, "bana_admin/site_stats.html", context)


def validate_members(request):
    context = {}
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})
    return render(request, 'bana_admin/validate_members.html', context)

def verify_bvm_prfl(request, profile_id):
    """
    Vue pour modifier le statut 'bvm_is_verified' d'un profil.
    Accessible via une requête POST.
    """
    if request.method == 'POST':
        profile = get_object_or_404(Profile, id=profile_id)

        if not profile.bvm_is_verified:
            profile.bvm_is_verified = True
            profile.save()
            messages.success(request, f'Le statut BVM pour {profile.user.username} a été validé avec succès.')
        else:
            messages.info(request, f'Le profil de {profile.user.username} avait déjà un BVM validé.')

        return redirect('bana_admin:validate_members')

    messages.error(request, 'Méthode de requête non autorisée.')
    return redirect('admin_panel')
    


def verify_profile_prfl(request, profile_id): #, profile_id
    """
    Nouvelle vue pour gérer la vérification du profil
    Vue pour modifier le statut 'prfl_is_verified' d'un profil.
    Accessible via une requête POST.
    """
    if request.method == 'POST':
        profile = get_object_or_404(Profile, id=profile_id)

        if not profile.prfl_is_verified:
            profile.prfl_is_verified = True
            profile.save()
            messages.success(request, f'Le statut de vérification PRFL pour {profile.user.username} a été mis à jour avec succès.')
        else:
            messages.info(request, f'Le profil de {profile.user.username} était déjà vérifié (PRFL).')

        # Rediriger l'utilisateur vers la page de liste des profils après la modification
        #return redirect('admin_panel') # Assurez-vous que c'est le nom de votre URL pour admin_views
        return redirect('bana_admin:validate_members')

    # Si la requête n'est pas POST, rediriger ou afficher une erreur
    messages.error(request, 'Méthode de requête non autorisée.')
    return redirect('admin_panel') # Rediriger même en cas de méthode incorrecte


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


