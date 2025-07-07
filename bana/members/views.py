from django.contrib.auth import logout
from .forms import UserRegistrationForm, MembersForm, LoginForm, ReviewForm
from trajects.models import ProposedTraject, ResearchedTraject, Reservation
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Review
from .forms import ReviewForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserRegistrationForm, MembersForm

# ===================== connexion ==================================================== 89
def register_user(request):
    
    print("=========== On est dans l' App/View :: members/register_user ")
    if request.user.is_authenticated:
        return redirect('/')

    user_form = UserRegistrationForm()
    members_form = MembersForm()

    if request.method == "POST":
        # print("+++++++++++++++++++++++++++",request.POST)
        user_form = UserRegistrationForm(request.POST)
        members_form = MembersForm(request.POST)

        if user_form.is_valid() and members_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            member = members_form.save(commit=False)
            member.memb_user_fk = user
            member.save()

            # Sauvegarder les langues choisies si c'est un ManyToManyField
            members_form.save_m2m()

            user = authenticate(request, username=user_form.cleaned_data['username'],
                                password=user_form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                messages.success(request, "Registration successful!")
                return redirect('home')
            else:
                messages.error(request, "Registration failed. Please try again.")
                return redirect('register')
        else:
            print("error", user_form.errors, members_form.errors)

    return render(request, 'members/authenticate/register_page.html',
                  {'user_form': user_form, 'members_form': members_form})


def login_user(request):
   
    print("=========== On est dans l' App/View :: members/login_user ")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
                return redirect('login')
    else:
        form = LoginForm()
    return render(request, 'members/authenticate/login_page.html', {'form': form})

def logout_user(request):
   
    print("=========== On est dans l' App/View :: members/logout_user ")

    logout(request)
    return redirect('home')

# ===================== profile ====================================================== 89
@login_required
def profile(request):
    '''
    '''
    print("=========== On est dans l' App/View :: members/profile ")

    if request.user.is_authenticated:
        member = request.user.members
        proposed_trajects = ProposedTraject.get_proposed_trajects_by_member(member)
        researched_trajects = ResearchedTraject.get_researched_trajects_by_member(member)
        reservations = Reservation.get_reservation_by_member(member)
        # Récupérer les langues associées au membre
        languages = member.languages.all()
        # Récupérer les avis reçus
        reviews = Review.objects.filter(reviewed_user=request.user)
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        context = {
            'proposed_trajects': proposed_trajects,
            'researched_trajects': researched_trajects,
            'reservations': reservations,
            'languages': languages,
            'reviews': reviews,
            'average_rating': round(average_rating, 1),
        }
    else:
        context = {}

    return render(request, 'members/profile.html', context)

@login_required
def profile_user(request, user_id=None):
    '''
    Affiche le profil d'un utilisateur et permet de laisser/modifier une note
    '''
    print("=========== On est dans l' App/View :: members/profile_user ")

    if user_id and user_id == request.user.id:
        return redirect('profile')

    user = get_object_or_404(User, id=user_id) if user_id else request.user
    reviews = Review.objects.filter(reviewed_user=user)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    existing_review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()
    allow_review = existing_review is None

    #  Vérifier si l'utilisateur veut modifier son avis
    is_editing = 'edit_review' in request.GET and existing_review

    #  Initialisation du formulaire
    form = ReviewForm(instance=existing_review if is_editing else None)

    #  Gestion de la soumission du formulaire (ajout ou modification)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review if is_editing else None)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed_user = user
            review.save()
            messages.success(request, "Votre note a été mise à jour.")
            return redirect('profile_user', user_id=user.id)

    return render(request, 'members/profile_user.html', {
        'user': user,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'allow_review': allow_review,
        'existing_review': existing_review,
        'form': form,
        'is_editing': is_editing,  #  Indicateur pour savoir si l'on modifie
    })

###################################################################################### 89
@login_required
def delete_review(request, user_id):
    '''
    Supprime la note d'un utilisateur
    '''
    print("=========== On est dans l' App/View :: members/delete_review ")

    user = get_object_or_404(User, id=user_id)
    review = Review.objects.filter(reviewer=request.user, reviewed_user=user).first()

    if review:
        review.delete()
        messages.success(request, "Votre note a été supprimée.")

    return redirect('profile_user', user_id=user.id)
