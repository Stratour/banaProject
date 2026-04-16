from math import floor

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmation
from django.utils.translation import gettext as _
from .utils import send_change_email_confirmation
from django.views.decorators.http import require_http_methods
import logging
from django.conf import settings
from django.db import transaction

from allauth.account.internal import flows
from allauth.account.views import PasswordChangeView

from .forms import ProfileUpdateForm, ChildForm, ReviewForm, UserUpdateForm, FavoriteAddressForm
from accounts.models import Profile, Child, Review, FavoriteAddress
from stripe_sub.models import Subscription

logger = logging.getLogger(__name__)

# ==================== LOGIN / LOGOUT / PROFILE ==================== #

def get_onboarding_steps(user, profile):
    """Retourne la liste des étapes d'onboarding avec leur état."""
    is_abonned = Subscription.is_user_abonned(user)
    # La CI vérifiée valide automatiquement le prénom/nom (Stripe Identity les met à jour)
    has_name = bool(user.first_name and user.last_name) or profile.ci_is_verified

    steps = [
        {
            "label": _("Renseigner votre prénom et nom"),
            "done": has_name,
            "url": reverse("accounts:profile_edit"),
            "detail": _("Requis pour accéder aux trajets"),
        },
        {
            "label": _("Souscrire un abonnement"),
            "done": is_abonned,
            "url": reverse("subscription"),
            "detail": _("Requis pour voir les profils et réserver"),
        },
    ]

    if is_abonned:
        steps += [
            {
                "label": _("Vérifier votre identité (CI)"),
                "done": profile.ci_is_verified,
                "url": reverse("create_verification_session"),
                "detail": _("Obligatoire pour réserver"),
                "method": "post",
            },
            {
                "label": _("Déposer votre certificat BVM"),
                "done": bool(profile.document_bvm),
                "url": reverse("accounts:profile_edit"),
                "detail": _("En attente de validation admin"),
            },
            {
                "label": _("Ajouter une photo de profil"),
                "done": bool(profile.profile_picture),
                "url": reverse("accounts:profile_edit"),
                "detail": _("Requise pour utiliser votre abonnement"),
            },
        ]

    if profile.service == "Parent":
        steps.append({
            "label": _("Ajouter un enfant"),
            "done": user.children.exists(),
            "url": reverse("accounts:add_child"),
            "detail": _("Nécessaire pour créer une recherche de trajet"),
        })

    return steps

@login_required(login_url="/accounts/login/")
def profile_view(request):
    """Page profil (tableau de bord). S’assure qu’un Profile existe et le passe au template."""
    profile, _created = Profile.objects.get_or_create(user=request.user)

    # Message de bienvenue au premier passage après inscription
    if not profile.onboarding_seen:
        profile.onboarding_seen = True
        profile.save(update_fields=["onboarding_seen"])
        messages.success(request, _("Bienvenue sur BanaCommunity ! Complétez votre profil pour commencer."))

    onboarding_steps = get_onboarding_steps(request.user, profile)
    onboarding_complete = all(s["done"] for s in onboarding_steps)

    return render(request, "account/profile/profile.html", {
        "profile": profile,
        "onboarding_steps": onboarding_steps,
        "onboarding_complete": onboarding_complete,
        "page_title": _("Mon profil"),
    })


@login_required
def profile_user(request, user_id=None):
    """Profil public d’un utilisateur + notes/avis. Fonctionne aussi pour son propre profil."""
    user = get_object_or_404(User.objects.select_related('profile'), id=user_id)
    is_own_profile = (user == request.user)

    reviews = Review.objects.filter(reviewed_user=user)
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    # Calcul étoiles
    full_stars = int(floor(average_rating))
    has_half_star = (average_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

    existing_review = None
    allow_review = False
    is_editing = False
    form = None

    if not is_own_profile:
        existing_review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()
        allow_review = existing_review is None
        is_editing = "edit_review" in request.GET and existing_review
        form = ReviewForm(instance=existing_review if is_editing else None)

        if request.method == "POST":
            form = ReviewForm(request.POST, instance=existing_review if is_editing else None)
            if form.is_valid():
                review = form.save(commit=False)
                review.reviewer = request.user
                review.reviewed_user = user
                review.save()
                messages.success(request, "Votre note a été mise à jour.")
                return redirect("accounts:profile_user", user_id=user.id)

    return render(
        request,
        "account/profile/profile_user.html",
        {
            "user": user,
            "is_own_profile": is_own_profile,
            "reviews": reviews,
            "average_rating": round(average_rating, 1),
            "reviews_count": reviews_count,
            "full_stars": full_stars,
            "has_half_star": has_half_star,
            "empty_stars": empty_stars,
            "allow_review": allow_review,
            "existing_review": existing_review,
            "form": form,
            "is_editing": is_editing,
        },
    )


@login_required
def delete_review(request, user_id):
    """Supprime l’avis de l’utilisateur connecté sur `user_id`."""
    user = get_object_or_404(User, id=user_id)
    review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()
    if review:
        review.delete()
        messages.success(request, "Votre note a été supprimée.")
    return redirect("accounts:profile_user", user_id=user.id)


@login_required
def profile_public(request):
    """Fragment/section profil public de l’utilisateur connecté."""
    Profile.objects.get_or_create(user=request.user)
    
    # Récupération des avis reçus
    reviews = Review.objects.filter(reviewed_user=request.user)
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    # Calcul des étoiles
    full_stars = int(floor(average_rating))
    has_half_star = (average_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

    context = {
        "reviews": reviews,
        "reviews_count": reviews_count,
        "average_rating": round(average_rating, 1),
        "full_stars": full_stars,
        "has_half_star": has_half_star,
        "empty_stars": empty_stars,
    }
        
    return render(request, "account/partials/profile_public.html", context)


@login_required
def profile_info(request):
    """Fragment/section profil privé de l’utilisateur connecté."""
    Profile.objects.get_or_create(user=request.user)
    return render(request, "account/partials/profile_info.html")


@login_required
def profile_edit(request):
    """Edition du profil (version simple : un seul `ProfileUpdateForm`)."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user
    
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        user_form = UserUpdateForm(request.POST, instance=user)
        user_form.fields['email'].disabled = True

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            profile.update_profile_verified()
            messages.success(request, "Profil mis à jour.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=profile)
        user_form = UserUpdateForm(instance=user)
        user_form.fields['email'].disabled = True
    return render(
        request,
        "account/profile/profile_edit.html",
        {"form": form, "user_form": user_form},
    )


@login_required
def profile_security(request):
    """Page Sécurité & connexion (sans HTMX)."""
    pending = EmailAddress.objects.filter(
        user=request.user, verified=False, primary=False
    ).values_list("email", flat=True).first()
    password_errors = request.session.pop('password_form_errors', {})
    return render(request, "account/profile/profile_security.html", {
        "pending_email": pending,
        "password_errors": password_errors,
        "page_title": _("Sécurité & connexion"),
    })


@login_required
def deactivate_account(request):
    """Désactive le compte puis déconnecte l’utilisateur."""
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.save()
        messages.success(request, "Votre compte a été désactivé avec succès.")
        return redirect("accounts:logout")
    return redirect("accounts:profile_security")

@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté !")
    return redirect("home")


# ==================== PASSWORD CHANGE (Allauth) ==================== #

class CustomPasswordChangeView(PasswordChangeView):
    """Utilise la vue Allauth et revient sur la page sécurité après succès."""
    success_url = reverse_lazy("accounts:profile_security")

    def form_valid(self, form):
        form.save()
        flows.password_change.finalize_password_change(self.request, form.user)
        messages.success(self.request, "Mot de passe mis à jour.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        self.request.session['password_form_errors'] = {
            field: list(errors) for field, errors in form.errors.items()
        }
        return redirect(reverse_lazy("accounts:profile_security"))


# ==================== EMAIL (affichage / modification) ==================== #

@login_required
def email_display(request):
    """Ancienne page/email (utile si référencée)."""
    user = request.user
    email = user.email if user.email else "Aucun email associé"
    return render(request, "account/email_display.html", {"email": email})


@login_required
@require_http_methods(["POST"])
def email_edit(request):
    """Gère le changement d'adresse email"""
    new_email = request.POST.get('email')
    
    if not new_email:
        messages.error(request, _("Veuillez saisir une adresse email valide."))
        return redirect('accounts:profile_security')
    
    if new_email == request.user.email:
        messages.info(request, _("Cette adresse email est déjà votre adresse actuelle."))
        return redirect('accounts:profile_security')
    
    # Vérifier si l'email n'existe pas déjà
    if EmailAddress.objects.filter(email=new_email).exists():
        messages.error(request, _("Cette adresse email est déjà utilisée."))
        return redirect('accounts:profile_security')
    
    # Supprimer toute demande de changement précédente non confirmée
    EmailAddress.objects.filter(
        user=request.user, 
        verified=False, 
        primary=False
    ).delete()
    
    # Créer une nouvelle EmailAddress non vérifiée
    email_address = EmailAddress.objects.create(
        user=request.user,
        email=new_email,
        verified=False,
        primary=False
    )
    
    # Envoyer l'email de confirmation personnalisé
    if send_change_email_confirmation(request, request.user, new_email):
        messages.success(request, _("Un email de confirmation a été envoyé à votre nouvelle adresse."))
    else:
        messages.error(request, _("Erreur lors de l'envoi de l'email de confirmation."))
    
    return redirect('accounts:profile_security')

@login_required
def email_change_confirm(request, key):
    try:
        confirmation = EmailConfirmation.objects.get(key=key)
        email_address = confirmation.email_address

        if request.user != email_address.user:
            messages.error(request, _("Ce lien n'est pas valide pour cet utilisateur."))
            return redirect("accounts:profile_security")

        # Confirme l'email
        confirmation.confirm(request)

        # Allauth ne met pas automatiquement à jour user.email quand primary=False
        # On force la promotion du nouvel email en adresse principale
        email_address.refresh_from_db()
        if email_address.verified:
            with transaction.atomic():
                request.user.emailaddress_set.exclude(pk=email_address.pk).update(primary=False)
                email_address.primary = True
                email_address.save(update_fields=["primary"])
                request.user.email = email_address.email
                request.user.save(update_fields=["email"])
            messages.success(request, _("Votre adresse e-mail a été mise à jour."))
        else:
            messages.error(request, _("La confirmation a échoué. Veuillez réessayer."))

        return redirect("accounts:profile_security")

    except EmailConfirmation.DoesNotExist:
        messages.error(request, _("Ce lien de confirmation n'est plus valide."))
        return redirect("accounts:profile_security")

def redirect_after_email_confirmation(request):
    # Récupère l'URL de redirection stockée dans la session
    redirect_url = request.session.pop('redirect_after_confirmation', None)
    if redirect_url:
        return redirect(redirect_url)
    return redirect(settings.LOGIN_REDIRECT_URL)

@login_required
def profile_children_view(request):
    """Affiche les enfants liés à l’utilisateur connecté."""
    children = request.user.children.all()
    return render(request, "account/profile/profile_children.html", {"children": children, "page_title": _("Mes enfants")})


@login_required
def add_child_view(request):
    """
    Ajoute un enfant et affiche la liste.
    Supporte un paramètre `next` pour rediriger après l'ajout.
    """
    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.chld_user = request.user
            child.save()
            form.save_m2m()
            messages.success(request, "Enfant ajouté avec succès.")
            if next_url:
                return redirect(next_url)
            return redirect("accounts:profile_child")
    else:
        form = ChildForm()

    children = request.user.children.all()
    return render(request, "account/profile/profil_add_child.html", {
        "form": form,
        "children": children,
        "next_url": next_url,
    })

@login_required
def delete_child_view(request, child_id):
    """
    Supprime un enfant de l'utilisateur connecté et redirige vers la page principale avec un message.
    """
    child = get_object_or_404(Child, id=child_id, chld_user=request.user)
    if request.method == "POST":
        child.delete()
        messages.success(request, "Enfant supprimé avec succès.")
        return redirect("accounts:profile_child")

    # En cas d'accès direct GET, rediriger vers la page principale
    messages.error(request, "Action non autorisée.")
    return redirect("accounts:profile_child")


@login_required
def profile_addresses(request):
    addresses = FavoriteAddress.objects.filter(user=request.user)
    return render(request, "account/profile/profile_addresses.html", {"addresses": addresses, "page_title": _("Mes adresses")})


@login_required
def create_address(request):
    if request.method == "POST":
        form = FavoriteAddressForm(request.POST)

        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()

            messages.success(request, "Adresse favorite enregistrée.")
            return redirect("accounts:profile_addresses")

        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = FavoriteAddressForm()

    return render(
        request,
        "account/profile/profile_add_address.html",
        {
            "form": form,
            "mode": "create",
        },
    )


@login_required
def delete_address(request, uid):
    addr = get_object_or_404(FavoriteAddress, user=request.user, uid=uid)

    if request.method == "POST":
        addr.delete()
        messages.success(request, "Adresse favorite supprimée.")
        return redirect("accounts:profile_addresses")

    return redirect("accounts:profile_addresses")
