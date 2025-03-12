from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ProposedTraject, ResearchedTraject, Members, Traject
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
from django.core.exceptions import PermissionDenied
from .utils.geocoding import get_autocomplete_suggestions
from django.db.models import Q




# ===================== listing ======================== #

def all_trajects(request):
    active_tab = request.GET.get('active_tab', 'proposed')
    start_adress = request.GET.get('start_adress', '').strip()
    end_adress = request.GET.get('end_adress', '').strip()
    
    # Base querysets
    proposed_trajects_list = ProposedTraject.objects.all().order_by('-departure_time')
    researched_trajects_list = ResearchedTraject.objects.select_related('traject').all().order_by('-departure_time')
    
    # Filtering based on search inputs
    if start_adress:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__start_adress__icontains=start_adress) |
            Q(traject__start_street__icontains=start_adress) |
            Q(traject__start_locality__icontains=start_adress)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__start_adress__icontains=start_adress) |
            Q(traject__start_street__icontains=start_adress) |
            Q(traject__start_locality__icontains=start_adress)
        )
    
    if end_adress:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__end_adress__icontains=end_adress) |
            Q(traject__end_street__icontains=end_adress) |
            Q(traject__end_locality__icontains=end_adress)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__end_adress__icontains=end_adress) |
            Q(traject__end_street__icontains=end_adress) |
            Q(traject__end_locality__icontains=end_adress)
        )
    
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
        'start_adress': start_adress,
        'end_adress': end_adress,
    }
    return render(request, 'trajects/trajects_page.html', context)


def autocomplete_view(request):
    """
    Vue pour gérer l'autocomplétion côté backend.
    """
    query = request.GET.get("query")  # Récupère le texte saisi par l'utilisateur
    if not query:
        return JsonResponse({"error": "Le champ 'query' est requis."}, status=400)

    suggestions = get_autocomplete_suggestions(query)
    if isinstance(suggestions, str):  # Si c'est une erreur
        return JsonResponse({"error": suggestions}, status=500)

    return JsonResponse({"suggestions": suggestions}, status=200)




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
def proposed_traject(request, researchesTraject_id=None):
    researched_traject = None
    if researchesTraject_id:
        try:
            researched_traject = ResearchedTraject.objects.get(id=researchesTraject_id)
            traject= Traject.objects.get(id=researched_traject.traject_id)
            print("++++++++++++++++++++++++++++++++++ " + str(traject))
            print("++++++++++++++++++++++++++++++++++ " + str(researched_traject.date))

        except Traject.DoesNotExist:
            pass  # Si le trajet n'existe pas, continue sans données pré-remplies

    initial_data = {}
    if researched_traject:
        initial_data = {
            'start_adress': traject.start_adress or f"{traject.start_street}, {traject.start_locality} {traject.start_country}",
            'end_adress': traject.end_adress or f"{traject.end_street}, {traject.end_locality} {traject.end_country}",
            'details': researched_traject.details,
            'number_of_places': researched_traject.number_of_places,
            'language': researched_traject.language.all(),
            'departure_time': researched_traject.departure_time,
            'arrival_time': researched_traject.arrival_time,
            'date': researched_traject.date,
            'transport_modes': researched_traject.transport_modes.all(),
        }

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
            print("Traject Form Errors:", traject_form.errors)
            print("Proposed Form Errors:", proposed_form.errors)
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
    else:
        traject_form = TrajectForm(initial=initial_data)
        proposed_form = ProposedTrajectForm(initial=initial_data)

    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form,
        'researched_traject': researched_traject  # Passer l'objet pour savoir si on a des données
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
            print("================Traject Form Errors:", traject_form.errors)
            print("================Proposed Form Errors:", researched_form.errors)
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