from django.contrib  import messages
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from allauth.account.views import PasswordChangeView
from .forms import UserUpdateForm, ProfileUpdateForm
from accounts.models import Profile

from allauth.account.internal import flows

@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté !")
    return redirect("/")

@login_required
def profile_user(request):
    
    profile, created = Profile.objects.get_or_create(user=request.user)
   
    return render(request, 'account/profile.html', {
        'user': request.user,  
        'profile': profile  
    })
@login_required
def profile_overview(request):
    '''
    Retourne les données de la table Profile de l'utilisateur connecté
    '''
    qs = Profile.objects.filter(user = request.user)
    context = {
        'profile': qs,
    }
    return render(request, 'account/profile_overview.html', context)


class CustomPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        print("==========form_valid : mot de passe changé=====")
        form.save()
        flows.password_change.finalize_password_change(self.request, form.user)

        if self.request.headers.get("HX-Request"): # Vérifie si la reqête est envoyée par HTMX
            response = HttpResponse()
            response['HX-Redirect'] = '/accounts/profile/' # redirection gérée par HTMX
            return response
        
        return redirect('/accounts/') # fallback non HTMX (fonctionne sans, mais important de le mettre...)

@login_required
def update_user(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':

        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
   
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()     
            profile_form.save() 
            messages.success(request, "Profile mis à jour !")
            return redirect('/accounts/profile')
        else:            
            print(user_form.errors)
            print(profile_form.errors)  

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'account/update_user.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })    

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    return render(request, 'account/profile.html', {
        'user': request.user,  # Données de l'utilisateur
        'profile': profile  # Données du profil
    })