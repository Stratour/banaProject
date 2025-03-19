from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ProposedTraject, ResearchedTraject, Members, Traject, Reservation, TransportMode
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions
from django.db.models import Q
from django.conf import settings
from datetime import datetime



# ===================== listing ======================== #

def all_trajects(request):
    active_tab = request.GET.get('active_tab', 'proposed')
    start_adress = request.GET.get('start_adress', '').strip()
    end_adress = request.GET.get('end_adress', '').strip()
    date_str = request.GET.get('date', '').strip()
    transport_modes = request.GET.getlist('transport_modes')  # Récupérer les modes de transport sélectionnés

    # Base querysets
    proposed_trajects_list = ProposedTraject.objects.all().order_by('-departure_time')
    researched_trajects_list = ResearchedTraject.objects.select_related('traject').all().order_by('-departure_time')

    # Récupérer les objets TransportMode correspondants
    transport_modes_objs = []
    if transport_modes:
        try:
            transport_modes_objs = TransportMode.objects.filter(name__in=transport_modes)
        except ObjectDoesNotExist:
            transport_modes_objs = []

    # Filtering based on start and end addresses
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

    # Filtering based on date
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # Format de la date
            proposed_trajects_list = proposed_trajects_list.filter(date=date_obj)
            researched_trajects_list = researched_trajects_list.filter(date=date_obj)
        except ValueError:
            pass  # Si la date est mal formée, on ignore le filtrage

    # Filtering based on transport modes
    if transport_modes_objs:
        proposed_trajects_list = proposed_trajects_list.filter(
            traject__proposedtraject__transport_modes__in=transport_modes_objs
        )
        researched_trajects_list = researched_trajects_list.filter(
            traject__researchedtraject__transport_modes__in=transport_modes_objs
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
        'date': date_str,
        'transport_modes': transport_modes,
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
    print(suggestions)
    if isinstance(suggestions, str):  # Si c'est une erreur
        return JsonResponse({"error": suggestions}, status=500)

    return JsonResponse({"suggestions": suggestions}, status=200)




# ===================== reservation page ======================== #
""""
@login_required
def reserve_traject(request, id):
    traject = get_object_or_404(ProposedTraject, id=id)
    print("++++++++++++++++++++++ traject " + str(traject))
    user_member = Members.objects.get(memb_user_fk=request.user)
    is_creator = traject.member == user_member
    print("++++++++++++++++++++++ traject.id " + str( traject.id))
    print("++++++++++++++++++++++ traject.traject_id ' " + str( traject.traject_id))

    context = {
        'traject': traject,
        'is_creator': is_creator,
    }
    if is_creator:
        print('================ if')
        # Add the list of reservation requests if the user is the creator
        # Assuming you have a model for reservations, replace `ReservationRequest` with the actual model name
        reservation_requests = ["member1","member2","member3"] #ReservationRequest.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        print('================ else')
        # Add any other context needed for non-creator users
        reservation_count = 3 #ReservationRequest.objects.filter(traject=traject).count()
        context['reservation_count'] = reservation_count

    return render(request, 'trajects/reserve_traject.html', context)
"""


@login_required
def reserve_traject(request, id):
    traject = get_object_or_404(ProposedTraject, id=id)
    user_member = Members.objects.get(memb_user_fk=request.user)
    is_creator = traject.member == user_member

    # Si l'utilisateur n'est pas le créateur
    if not is_creator:
        if request.method == 'POST':
            # Récupérer le nombre de places demandées
            try:
                num_places = int(request.POST.get('num_places'))
            except (ValueError, TypeError):
                num_places = 0

            # Vérifier si le nombre de places est valide
            if num_places <= 0:
                messages.error(request, "Le nombre de places doit être supérieur à 0.")
            elif num_places > int(traject.number_of_places):
                messages.error(request, "Il n'y a pas assez de places disponibles pour ce trajet.")
            else:
                # Créer la réservation
                reservation = Reservation.objects.create(
                    member=user_member,
                    traject=traject,
                    number_of_places=num_places
                )

                traject.save()

                # Récupérer l'email de l'utilisateur et du créateur
                user_email = request.user.email
                creator_email = traject.member.memb_user_fk.email

                # Afficher les emails dans la console pour débogage
                print(f"Email de l'utilisateur (membre) : {user_email}")
                print(f"Email du créateur du trajet : {creator_email}")

                # Envoi d'une notification par email au membre
                send_mail(
                    'Confirmation de votre demande de réservation',
                    f'Bonjour {request.user.username},\n\nVotre demande de réservation de {num_places} places pour le trajet "{traject.traject}" est en attente de confirmation.\n\nMerci.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user_email]
                )

                # Envoi d'une notification par email au créateur du trajet
                send_mail(
                    'Nouvelle demande de réservation',
                    f'Bonjour {traject.member.memb_user_fk.username},\n\nUn membre a fait une demande de réservation pour {num_places} places sur le trajet "{traject.traject}".\nVeuillez consulter la demande pour l\'approuver ou la refuser.\n\nMerci.',
                    settings.DEFAULT_FROM_EMAIL,
                    [creator_email]
                )

                messages.success(request, f'Votre demande de réservation de {num_places} places est une attente de confirmation!')
                return redirect('profile')  # Redirige vers une page de confirmation ou ailleurs

    context = {
        'traject': traject,
        'is_creator': is_creator,
    }

    if is_creator:
        reservation_requests = Reservation.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        reservation_count = Reservation.objects.filter(traject=traject).count()  # Remplacer par le nombre réel de réservations
        context['reservation_count'] = reservation_count

    return render(request, 'trajects/reserve_traject.html', context)


@login_required
def reserve_trajectResearched(request, researchedTraject_id):
    researched_traject = ResearchedTraject.objects.get(id=researchedTraject_id)
    traject = Traject.objects.get(id=researched_traject.traject_id)
    print("++++++++++++++++++++++++++++++++++ méthode appelé " + str(traject))
    print("++++++++++++++++++++++++++++++++++ " + str(researched_traject.date))
    trajectResearched = get_object_or_404(ResearchedTraject, id=researchedTraject_id)
    print("++++++++++++++++++++++ traject " + str(trajectResearched))
    user_member = Members.objects.get(memb_user_fk=request.user)
    is_creator = trajectResearched.member == user_member
    print("++++++++++++++++++++++ traject.id " + str(trajectResearched.id))
    print("++++++++++++++++++++++ traject.traject_id ' " + str(trajectResearched.traject_id))

    context = {
        'traject': trajectResearched,
        'is_creator': is_creator,
    }
    if is_creator:
        print('================ if')
        # Add the list of reservation requests if the user is the creator
        # Assuming you have a model for reservations, replace `ReservationRequest` with the actual model name
        reservation_requests = ["member1","member2","member3"] #ReservationRequest.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        print('================ else')
        # Add any other context needed for non-creator users
        reservation_count = 3 #ReservationRequest.objects.filter(traject=traject).count()
        context['reservation_count'] = reservation_count

    return render(request, 'trajects/reserve_traject.html', context)


@login_required
def manage_reservation(request, reservation_id, action):
    # Récupérer la réservation
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Vérifier si l'utilisateur est bien le créateur du trajet
    if not reservation.traject.member == Members.objects.get(memb_user_fk=request.user):
        messages.error(request, "You are not authorized to manage this reservation.")
        return redirect('profile')  # Ou une autre redirection appropriée

    # Gérer l'acceptation ou le rejet de la demande
    if action == 'accept':
        if reservation.status != 'pending':
            messages.error(request, "This reservation has already been processed.")
        else:
            # Récupérer l'objet ProposedTraject associé à la réservation
            proposed_traject = reservation.traject

            # Vérifier si le nombre de places demandées ne dépasse pas les places disponibles
            available_places = int(proposed_traject.number_of_places)
            requested_places = int(reservation.number_of_places)

            if requested_places > available_places:
                messages.error(request, "Not enough available places for this reservation.")
                return redirect('reserve_traject', id=reservation.traject.id)

            # Accepter la réservation, mettre à jour le statut
            reservation.status = 'confirmed'

            # Diminuer les places disponibles dans ProposedTraject
            proposed_traject.number_of_places = str(available_places - requested_places)
            proposed_traject.save()  # Sauvegarder l'objet ProposedTraject
            reservation.save()  # Sauvegarder la réservation

            messages.success(request, "Reservation accepted successfully.")
    elif action == 'reject':
        if reservation.status != 'pending':
            messages.error(request, "This reservation has already been processed.")
        else:
            # Rejeter la réservation
            reservation.status = 'canceled'
            reservation.save()
            messages.success(request, "Reservation rejected.")

    return redirect('reserve_traject', id=reservation.traject.id)

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