from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ProposedTraject, ResearchedTraject,Members
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
from django.core.exceptions import PermissionDenied




# ===================== listing ======================== #

def all_trajects(request):

    active_tab = request.GET.get('active_tab', 'proposed')
    proposed_trajects_list = ProposedTraject.objects.all().order_by('-departure_time')
    researched_trajects_list = ResearchedTraject.objects.select_related('traject').all().order_by('-departure_time')
    
    # Pagination for proposed trajects
    paginator1 = Paginator(proposed_trajects_list, 10)  # Show 10 proposed trajects per page
    page_number1 = request.GET.get('page1')
    proposed_trajects = paginator1.get_page(page_number1)
    
    # Pagination for researched trajects
    paginator2 = Paginator(researched_trajects_list, 10)  # Show 10 researched trajects per page
    page_number2 = request.GET.get('page2')
    researched_trajects = paginator2.get_page(page_number2)
    
    context = {
        'active_tab': active_tab,
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

# ===================== reservation page ======================== #

@login_required
def reserve_traject(request, id):
    traject = get_object_or_404(ProposedTraject, id=id)
    user_member = Members.objects.get(memb_user_fk=request.user)
    is_creator = traject.member == user_member

    context = {
        'traject': traject,
        'is_creator': is_creator,
    }

    if is_creator:
        # Add the list of reservation requests if the user is the creator
        # Assuming you have a model for reservations, replace `ReservationRequest` with the actual model name
        reservation_requests = ["member1","member2","member3"] #ReservationRequest.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        # Add any other context needed for non-creator users
        reservation_count = 3 #ReservationRequest.objects.filter(traject=traject).count()
        context['reservation_count'] = reservation_count

    return render(request, 'trajects/reserve_traject.html', context)


# ===================== CRUD ======================== #

@login_required
def proposed_traject(request):
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)
        if traject_form.is_valid() and proposed_form.is_valid():
            traject = traject_form.save()
            proposed = proposed_form.save(commit=False)
            proposed.traject = traject
            proposed.member = Members.objects.get(memb_user_fk=request.user)  # Assign the member
            proposed.save()
            proposed_form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Proposed Traject created successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
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
            searched.member = Members.objects.get(memb_user_fk=request.user)  # Assign the member
            searched.save()
            researched_form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Searched Traject created successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
    else:
        traject_form = TrajectForm()
        researched_form = ResearchedTrajectForm()
    context = {
        'traject_form': traject_form,
        'researched_form': researched_form
    }
    return render(request, 'trajects/searched_traject.html', context)


@login_required
def delete_traject(request, id, type):
    if type == 'proposed':
        traject = get_object_or_404(ProposedTraject, id=id, member=request.user.members)
    else:
        traject = get_object_or_404(ResearchedTraject, id=id, member=request.user.members)

    traject.delete()
    messages.success(request, 'Traject deleted successfully!')
    return redirect('profile')

@login_required
def modify_traject(request, id, type):
    if type == 'proposed':
        traject_instance = get_object_or_404(ProposedTraject, id=id, member=request.user.members)
        form_class = ProposedTrajectForm
    else:
        traject_instance = get_object_or_404(ResearchedTraject, id=id, member=request.user.members)
        form_class = ResearchedTrajectForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=traject_instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Traject updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
    else:
        form = form_class(instance=traject_instance)
    
    context = {
        'form': form,
        'traject': traject_instance
    }
    return render(request, 'trajects/modify_traject.html', context)