from django.contrib  import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from allauth.account.views import PasswordChangeView
from django.urls import reverse, reverse_lazy
from .forms import UserUpdateForm, ProfileUpdateForm
from accounts.models import Profile
from allauth.account.forms import AddEmailForm
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from allauth.account.internal import flows

#==================== LOGIN / LOGOUT / PROFILE (Nouveau)=========================#   

@login_required(login_url='/accounts/login/')
def profile_view(request):
    # Crée le profil s'il n'existe pas encore
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'account/profile/profile.html')

    
@login_required
def profile_public(request):
    """
    Affiche le profil public de l'utilisateur connecté.
    """
    # Crée le profil s'il n'existe pas encore
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'account/partials/profile_public.html')

@login_required
def profile_info(request):
    """
    Affiche le profil privé de l'utilisateur connecté.
    """
    # Crée le profil s'il n'existe pas encore
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'account/partials/profile_info.html')
    
@login_required
def profile_edit(request):
    """
    Permet à l'utilisateur de modifier son profil.
    Si la requête est POST, les données du formulaire sont traitées.
    Sinon, le formulaire est affiché avec les données actuelles de l'utilisateur.
    """
    # Crée le profil s'il n'existe pas encore
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès !")
            response = HttpResponse()
            response['HX-Redirect'] = reverse('accounts:profile')  # ou autre URL
            return response
        
        return render(request, 'account/partials/profile_edit.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
        
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

        return render(request, 'account/partials/profile_edit.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })   
    
@login_required
def profile_children(request):
    """
    Affiche la liste des enfants de l'utilisateur connecté.
    """
    return render(request, 'account/profile/profile_children.html')

@login_required
def profile_security(request):
    """
    Affiche les paramètres de sécurité et de connexion de l'utilisateur connecté.
    """
    return render(request, 'account/profile/profile_security.html')
    
@login_required
def deactivate_account(request):
    """
    Permet à l'utilisateur de désactiver son compte.
    Si la requête est POST, le compte est désactivé.
    Sinon, un message de confirmation est affiché.
    """
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        messages.success(request, "Votre compte a été désactivé avec succès.")
        return redirect('logout')
    else:
        return redirect(request, 'accounts:profile_security')

@login_required
def logout_user(request):
    print("=========== On est dans l' App/View :: accounts/logout_user")

    logout(request)
    messages.info(request, "Vous êtes déconnecté !")

    return redirect("/")

class CustomPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        form.save()
        flows.password_change.finalize_password_change(self.request, form.user)

        if self.request.headers.get("HX-Request"): # Vérifie si la reqête est envoyée par HTMX
            response = HttpResponse()
            response['HX-Redirect'] = '/accounts/profile/security/' # redirection gérée par HTMX
            return response
        
        return redirect('/accounts/') # fallback non HTMX (fonctionne sans, mais important de le mettre...)

@login_required
def email_display(request):
    """
    Affiche l'email de l'utilisateur connecté.
    """
    user = request.user
    email = user.email if user.email else "Aucun email associé"
    
    return render(request, 'account/email_display.html', {'email': email})


@login_required
def email_edit(request):
    if request.method == "POST":
        form = AddEmailForm(data=request.POST, user=request.user)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Vérifie si l’e-mail est déjà associé à un autre utilisateur
            if EmailAddress.objects.filter(email=email).exclude(user=request.user).exists():
                form.add_error("email", "Cette adresse e-mail est déjà utilisée.")
            else:
                # Crée l’objet s’il n’existe pas
                obj, created = EmailAddress.objects.get_or_create(
                    user=request.user,
                    email=email,
                    defaults={"verified": False, "primary": False}
                )

                if not obj.verified:
                    send_email_confirmation(request, request.user, signup=False, email=email)

            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("accounts:profile_security")
                return response

                return redirect("accounts:profile_security")
    else:
        form = AddEmailForm(user=request.user)

    return render(request, "account/email_change_form.html", {"form": form})