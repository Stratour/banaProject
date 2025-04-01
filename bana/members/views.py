from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Members
from .forms import UserRegistrationForm, MembersForm, LoginForm
from trajects.models import Traject, ProposedTraject, ResearchedTraject, Reservation

# ===================== connexion ======================== #
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserRegistrationForm, MembersForm


def register_user(request):
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
    logout(request)
    return redirect('home')


# ===================== profile ======================== #

@login_required
def profile(request):
    if request.user.is_authenticated:
        member = request.user.members
        proposed_trajects = ProposedTraject.get_proposed_trajects_by_member(member)
        researched_trajects = ResearchedTraject.get_researched_trajects_by_member(member)
        reservations = Reservation.get_reservation_by_member(member)
        # Récupérer les langues associées au membre
        languages = member.languages.all()

        context = {
            'proposed_trajects': proposed_trajects,
            'researched_trajects': researched_trajects,
            'reservations': reservations,
            'languages': languages,
        }
    else:
        context = {}

    return render(request, 'members/profile.html', context)
