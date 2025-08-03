from math import floor
from django.contrib  import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from allauth.account.views import PasswordChangeView
from django.urls import reverse, reverse_lazy
from .forms import UserUpdateForm, ProfileUpdateForm, ChildForm, ReviewForm
from accounts.models import Profile, Child, User, Review
from allauth.account.forms import AddEmailForm
from allauth.account.models import EmailAddress
#from allauth.account.utils import send_email_confirmation
from allauth.account.internal import flows
from allauth.account.adapter import get_adapter

#==================== LOGIN / LOGOUT / PROFILE (Nouveau)=========================#

@login_required(login_url='/accounts/login/')
def profile_view(request):
    # Crée le profil s'il n'existe pas encore
    Profile.objects.get_or_create(user=request.user)
    return render(request, 'account/profile/profile.html')


@login_required
def profile_user(request, user_id=None):
    if user_id and user_id == request.user.id:
        return redirect('accounts:profile')  # ou ton propre profil

    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(reviewed_user=user)
    reviews_count = reviews.count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    # Calcul des étoiles pour l'affichage
    full_stars = int(floor(average_rating))
    has_half_star = (average_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)
    existing_review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()
    allow_review = existing_review is None

    is_editing = 'edit_review' in request.GET and existing_review
    form = ReviewForm(instance=existing_review if is_editing else None)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review if is_editing else None)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed_user = user
            review.save()
            messages.success(request, "Votre note a été mise à jour.")
            return redirect('accounts:profile_user', user_id=user.id)

    return render(request, 'account/profile/profile_user.html', {
        'user': user,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'reviews_count': reviews_count,
        'full_stars': full_stars,
        'has_half_star': has_half_star,
        'empty_stars': empty_stars,
        'allow_review': allow_review,
        'existing_review': existing_review,
        'form': form,
        'is_editing': is_editing,
    })

@login_required
def delete_review(request, user_id):
    user = get_object_or_404(User, id=user_id)
    review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()
    if review:
        review.delete()
        messages.success(request, "Votre note a été supprimée.")
    return redirect('accounts:profile_user', user_id=user.id)
 
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
                    # send_email_confirmation(request, request.user, signup=False, email=email)
                    get_adapter(request).send_confirmation_mail(request, user)

            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("accounts:profile_security")
                return response

    else:
        form = AddEmailForm(user=request.user)

    return render(request, "account/email_change_form.html", {"form": form})


#==================== ADD CHILDREN TO A PROFILE =========================#
@login_required
def profile_children_view(request):
    # Récupérer tous les enfants liés à l'utilisateur connecté
    children = request.user.children.all() # ou Child.objects.filter(user=request.user)
    context = {
        'children': children
    }
    #return render(request, 'account/partials/profile_child.html', context)
    return render(request, 'account/profile/profile_children.html', context)

@login_required
def add_child_view(request):
    """
    Cette méthode affiche les enfants de l'utilisateur connecté sur sa page 'Profil'
    Il peut ajouter d'autres enfants s'il le souhaite
    !!! Les templates HTML se trouvent dans le dossier "account/profile/*.html"
    Il y a doublon avec le lien du menu 'Mes enfants' créé par Luca
    """
    if request.method == 'POST':
        form = ChildForm(request.POST)
        if form.is_valid():
            # Créer l'objet enfant sans le sauvegarder en base de données pour le moment
            child = form.save(commit=False)
            # Assigner l'utilisateur connecté comme parent de l'enfant
            child.chld_user = request.user
            # Sauvegarder l'objet complet en base de données
            child.save()
            # Rediriger vers la même page pour permettre d'ajouter un autre enfant
            return redirect('accounts:add_child') 
    else:
        form = ChildForm()

    # Récupérer et afficher les enfants déjà ajoutés sur la même page
    children = request.user.children.all()
    context = {
        'form': form,
        'children': children
    }
    #return render(request, 'account/partials/profil_add_child.html', context)
    return render(request, 'account/profile/profil_add_child.html', context)
