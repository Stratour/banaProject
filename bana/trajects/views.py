from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ProposedTraject, ResearchedTraject, Traject
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
# import requests  # Uncomment this when you need to use the coordinate API

def all_trajects(request):
    proposed_trajects_list = ProposedTraject.objects.all().order_by('-departure_time')
    researched_trajects_list = ResearchedTraject.objects.all().order_by('-departure_time')
    
    # Pagination for proposed trajects
    paginator1 = Paginator(proposed_trajects_list, 10)  # Show 10 proposed trajects per page
    page_number1 = request.GET.get('page1')
    proposed_trajects = paginator1.get_page(page_number1)
    
    # Pagination for researched trajects
    paginator2 = Paginator(researched_trajects_list, 10)  # Show 10 researched trajects per page
    page_number2 = request.GET.get('page2')
    researched_trajects = paginator2.get_page(page_number2)
    
    context = {
        'proposed_trajects': proposed_trajects,
        'researched_trajects': researched_trajects,
    }
    return render(request, 'trajects/trajects_page.html', context)

def search_trajects(request):
    start_city = request.GET.get('start_locality', '').strip()
    end_city = request.GET.get('end_locality', '').strip()
    
    # Get all trajects
    proposed_trajects = ProposedTraject.objects.all()
    researched_trajects = ResearchedTraject.objects.all()
    
    # Filter by start locality if provided
    if start_city:
        proposed_trajects = proposed_trajects.filter(traject__start_locality__icontains=start_city)
        researched_trajects = researched_trajects.filter(traject__start_locality__icontains=start_city)
    
    # Filter by end locality if provided
    if end_city:
        proposed_trajects = proposed_trajects.filter(traject__end_locality__icontains=end_city)
        researched_trajects = researched_trajects.filter(traject__end_locality__icontains=end_city)
    
    context = {
        'proposed_trajects': proposed_trajects,
        'researched_trajects': researched_trajects,
    }
    
    # Add a message if no matches are found
    if not proposed_trajects.exists() and not researched_trajects.exists():
        context.update({
            'no_match': True,
            'start_city': start_city,
            'end_city': end_city,
        })
    
    return render(request, 'trajects/trajects_page.html', context)





@login_required
def proposed_traject(request):
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)
        if traject_form.is_valid() and proposed_form.is_valid():
            traject = traject_form.save()
            proposed = proposed_form.save(commit=False)
            proposed.traject = traject
            proposed.save()
            proposed.member.add(request.user.members)
            messages.success(request, 'Proposed Traject created successfully!')
            return redirect('profile')
    else:
        traject_form = TrajectForm()
        proposed_form = ProposedTrajectForm()
    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form
    }
    return render(request, 'trajects/proposed_traject.html', context)

@login_required
def searched_traject(request):
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST)
        if traject_form.is_valid() and researched_form.is_valid():
            traject = traject_form.save()
            searched = researched_form.save(commit=False)
            searched.traject = traject
            searched.save()
            searched.member.add(request.user.members)
            messages.success(request, 'Searched Traject created successfully!')
            return redirect('profile')
    else:
        traject_form = TrajectForm()
        researched_form = ResearchedTrajectForm()
    context = {
        'traject_form': traject_form,
        'researched_form': researched_form
    }
    return render(request, 'trajects/searched_traject.html', context)



"""
# Uncomment this when ready to integrate the coordinate API
def get_coordinates(street, locality, country):
    # Example function to make an API call to get coordinates
    api_url = "https://api.example.com/get-coordinates"
    response = requests.get(api_url, params={'street': street, 'locality': locality, 'country': country})
    data = response.json()
    return f"{data['lat']}, {data['lng']}"
"""
