
# Create your views here.
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import InscriptionValidation # Assurez-vous d'importer votre modèle
from django.contrib.auth.models import User
from accounts.models import Profile # Importez votre modèle Profile



def bana_admin(request):
    print('================ bana_admin_views :: ')
    context = {}
    users = User.objects.all()
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})

    print('================== Users :: ', users)
    print('================== Profiles :: ', profiles)
    
    return render(request, 'bana_admin/bana_admin.html', context)


def admin_view(request):
    print('================ admin_views :: ')
    context = {}
    users = User.objects.all()
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})

    print('================== Users :: ', users)
    print('================== Profiles :: ', profiles)
    
    return render(request, 'bana_admin/admin_view.html', context)


def validate_members(request):
    print('================ admin_views :: ')
    context = {}
    users = User.objects.all()
    profiles = Profile.objects.all()
    context.update({'profiles': profiles})

    print('================== Users :: ', users)
    print('================== Profiles :: ', profiles)
    
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


