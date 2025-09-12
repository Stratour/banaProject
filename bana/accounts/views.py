from math import floor

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from allauth.account.forms import AddEmailForm
from allauth.account.internal import flows
from allauth.account.models import EmailAddress
from allauth.account.views import PasswordChangeView
from allauth.account.adapter import get_adapter

from .forms import ProfileUpdateForm, ChildForm, ReviewForm, UserUpdateForm
from accounts.models import Profile, Child, Review


# ==================== LOGIN / LOGOUT / PROFILE ==================== #

@login_required(login_url="/accounts/login/")
def profile_view(request):
    """Page profil (tableau de bord). S’assure qu’un Profile existe et le passe au template."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "account/profile/profile.html", {"profile": profile})


@login_required
def profile_user(request, user_id=None):
    """Profil public d’un autre utilisateur + notes/avis."""
    if user_id and user_id == request.user.id:
        return redirect("accounts:profile")

    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(reviewed_user=user)
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    # Calcul étoiles
    full_stars = int(floor(average_rating))
    has_half_star = (average_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

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
    return render(request, "account/partials/profile_public.html")


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
def profile_children(request):
    """Page enfants (menu profil)."""
    return render(request, "account/profile/profile_children.html")


@login_required
def profile_security(request):
    """Page Sécurité & connexion (sans HTMX)."""
    return render(request, "account/profile/profile_security.html")


@login_required
def deactivate_account(request):
    """Désactive le compte puis déconnecte l’utilisateur."""
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.save()
        messages.success(request, "Votre compte a été désactivé avec succès.")
        return redirect("logout")
    return redirect("accounts:profile_security")


@login_required
def logout_user(request):
    """Déconnexion."""
    logout(request)
    messages.info(request, "Vous êtes déconnecté !")
    return redirect("/")


# ==================== PASSWORD CHANGE (Allauth) ==================== #

class CustomPasswordChangeView(PasswordChangeView):
    """Utilise la vue Allauth et revient sur la page sécurité après succès."""
    success_url = reverse_lazy("accounts:profile_security")

    def form_valid(self, form):
        form.save()
        flows.password_change.finalize_password_change(self.request, form.user)
        messages.success(self.request, "Mot de passe mis à jour.")
        return redirect(self.get_success_url())


# ==================== EMAIL (affichage / modification) ==================== #

@login_required
def email_display(request):
    """Ancienne page/email (utile si référencée)."""
    user = request.user
    email = user.email if user.email else "Aucun email associé"
    return render(request, "account/email_display.html", {"email": email})


@login_required
def email_edit(request):
    """Change l’email (avec contrôle de collision) puis revient sur Sécurité."""
    if request.method == "POST":
        form = AddEmailForm(data=request.POST, user=request.user)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Email déjà pris par un autre user ?
            if EmailAddress.objects.filter(email=email).exclude(user=request.user).exists():
                form.add_error("email", "Cette adresse e-mail est déjà utilisée.")
            else:
                obj, created = EmailAddress.objects.get_or_create(
                    user=request.user,
                    email=email,
                    defaults={"verified": False, "primary": False},
                )
                if not obj.verified:
                    # Envoie email de confirmation
                    get_adapter(request).send_confirmation_mail(request, request.user, email=email)

                # Met à jour l’adresse sur l’objet user
                request.user.email = email
                request.user.save(update_fields=["email"])

            messages.success(request, "E-mail mis à jour. Vérifie ta boîte.")
        return redirect("accounts:profile_security")

    # GET (si tu gardes un formulaire séparé, sinon cette vue ne sera appelée qu’en POST)
    form = AddEmailForm(user=request.user)
    return render(request, "account/email_change_form.html", {"form": form})


# ==================== ENFANTS ==================== #

@login_required
def profile_children_view(request):
    """Affiche les enfants liés à l’utilisateur connecté."""
    children = request.user.children.all()
    return render(request, "account/profile/profile_children.html", {"children": children})


@login_required
def add_child_view(request):
    """
    Ajoute un enfant et affiche la liste.
    """
    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.chld_user = request.user
            child.save()
            return redirect("accounts:add_child")
    else:
        form = ChildForm()

    children = request.user.children.all()
    return render(request, "account/profile/profil_add_child.html", {"form": form, "children": children})


# ==================== OUTIL DE POPULATION (DEV) ==================== #

import json
import random

def pop_profile(request):
    """
    Outil dev : crée des profils de démonstration pour des utilisateurs lambda_*.
    """
    adresses_bruxelles = [
        {"line1": "Place de la Bourse", "city": "Bruxelles", "country": "BE", "postal_code": "1000"},
        {"line1": "Grand-Place", "city": "Bruxelles", "country": "BE", "postal_code": "1000"},
        {"line1": "Rue du Marché aux Herbes 61", "city": "Bruxelles", "country": "BE", "postal_code": "1000"},
        {"line1": "Avenue Louise 23", "city": "Ixelles", "country": "BE", "postal_code": "1050"},
        {"line1": "Rue de la Loi 1", "city": "Bruxelles", "country": "BE", "postal_code": "1000"},
        {"line1": "Chaussée de Wavre 25", "city": "Ixelles", "country": "BE", "postal_code": "1050"},
        {"line1": "Rue Neuve", "city": "Bruxelles", "country": "BE", "postal_code": "1000"},
        {"line1": "Chaussée de Charleroi 154", "city": "Saint-Gilles", "country": "BE", "postal_code": "1060"},
        {"line1": "Avenue des Saisons 123", "city": "Ixelles", "country": "BE", "postal_code": "1050"},
        {"line1": "Place Flagey", "city": "Ixelles", "country": "BE", "postal_code": "1050"},
        {"line1": "Place Brugmann 18", "city": "Ixelles", "country": "BE", "postal_code": "1050"},
    ]

    services = ["parent", "yaya"]
    transports = ["voiture", "transport en commun", "vélo", "à pied"]

    users = list(User.objects.filter(username__startswith="lambda_"))
    random.shuffle(adresses_bruxelles)

    profiles_to_create = [
        Profile(
            user=user,
            address=json.dumps(adresses_bruxelles.pop()),
            ci_is_verified=True,
            service=random.choice(services),
            transport_modes=random.sample(transports, random.randint(1, 3)),
            bio=f"Bonjour, je suis {user.first_name}. Je recherche des services de garde d'enfants.",
            phone=f"04{random.randint(70, 79)}{random.randint(100000, 999999)}",
        )
        for user in users
    ]

    Profile.objects.bulk_create(profiles_to_create)

    print(f"Création de {len(profiles_to_create)} profils terminée.")
    for p in Profile.objects.all():
        addr = json.loads(p.address)
        print(f"Profil pour '{p.user.username}' créé. Adresse: {addr['line1']}, {addr['city']}.")
