from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ProposedTraject, ResearchedTraject, Members, Traject, Reservation, TransportMode
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions
from django.db.models import Q
from django.conf import settings
from datetime import datetime
from dateutil.rrule import rrule, WEEKLY, DAILY
from datetime import datetime, timedelta
from datetime import timedelta


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

                messages.success(request,
                                 f'Votre demande de réservation de {num_places} places est une attente de confirmation!')
                return redirect('profile')  # Redirige vers une page de confirmation ou ailleurs

    context = {
        'traject': traject,
        'is_creator': is_creator,
    }

    if is_creator:
        reservation_requests = Reservation.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        reservation_count = Reservation.objects.filter(
            traject=traject).count()  # Remplacer par le nombre réel de réservations
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
        reservation_requests = ["member1", "member2", "member3"]  # ReservationRequest.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        print('================ else')
        # Add any other context needed for non-creator users
        reservation_count = 3  # ReservationRequest.objects.filter(traject=traject).count()
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
from datetime import datetime, timedelta
from django.db import IntegrityError

from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ResearchedTraject, Traject, ProposedTraject, Members
from .forms import TrajectForm, ProposedTrajectForm


@login_required
def proposed_traject(request, researchesTraject_id=None):
    researched_traject = None
    traject = None

    # Tentative de récupération des informations de trajet si l'ID est fourni
    if researchesTraject_id:
        try:
            researched_traject = ResearchedTraject.objects.get(id=researchesTraject_id)
            traject = Traject.objects.get(id=researched_traject.traject_id)
        except (ResearchedTraject.DoesNotExist, Traject.DoesNotExist) as e:
            print(f"Error fetching traject: {e}")

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

            # Récupération des données du formulaire
            recurrence_type = proposed_form.cleaned_data['recurrence_type']
            recurrence_interval = proposed_form.cleaned_data['recurrence_interval']
            recurrence_days = request.POST.getlist('tr_weekdays[]')
            print("===============================   recurrence_days ", recurrence_days)
            date_debut = proposed_form.cleaned_data['date_debut']
            date_fin = proposed_form.cleaned_data['date_fin']
            # Récupération des données du formulaire
            departure_time = request.POST.get('departure_time')
            arrival_time = request.POST.get('arrival_time')
            number_of_places = request.POST.get('number_of_places')
            transport_modes = request.POST.get('transport_modes')
            details = request.POST.get('details')

            # Convertir les dates de début et de fin en objets datetime
            if date_debut:
                date_debut = datetime.strptime(str(date_debut), '%Y-%m-%d')
            if date_fin:
                date_fin = datetime.strptime(str(date_fin), '%Y-%m-%d')

            # Liste pour stocker les trajets récurrents à insérer
            recurrent_trajects = []

            # Fonction pour générer les dates récurrentes
            def generate_recurrent_dates(start_date, end_date, recurrence_type, recurrence_interval=None,
                                         specific_days=None):
                current_date = start_date
                recurrent_dates = []

                while current_date <= end_date:
                    if recurrence_type == 'weekly_interval':
                        recurrent_dates.append(current_date.date())
                        current_date += timedelta(days=recurrence_interval)
                    elif recurrence_type == 'specific_days':
                        # Vérifier si le jour actuel correspond à un des jours spécifiques sélectionnés
                        print("======================== current_date.weekday ", current_date.weekday())
                        weekday = str(current_date.weekday() + 1)  # Convertir le weekday en chaîne de caractères
                        if weekday in specific_days:  # weekday() retourne 0=Monday, donc +1 pour correspondre à l'index
                            print(current_date.date())
                            recurrent_dates.append(current_date.date())
                        current_date += timedelta(days=1)
                        print("====================== current_date ", current_date)
                return recurrent_dates

            # Génération des dates récurrentes en fonction du type
            if recurrence_type == 'weekly_interval':
                if recurrence_interval and date_debut:
                    date_fin = date_debut + timedelta(weeks=recurrence_interval)  # Calcul de la date de fin
                recurrent_dates = generate_recurrent_dates(date_debut, date_fin, recurrence_type, recurrence_interval)
            elif recurrence_type == 'specific_days' and recurrence_days:
                recurrent_dates = generate_recurrent_dates(date_debut, date_fin, recurrence_type,
                                                           specific_days=recurrence_days)

            # Enregistrer tous les trajets récurrents en une seule opération
            for date in recurrent_dates:
                print("============================   date à ajouter ", date)

                proposed_traject = ProposedTraject(
                    member_id=Members.objects.get(memb_user_fk=request.user).id,  # Récupère l'id du membre
                    traject_id=traject.id,  # Assure-toi que tu as la variable `traject` dans ton contexte
                    date=date,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    number_of_places=number_of_places,
                    details=details,
                    recurrence_type=recurrence_type,
                    recurrence_interval=recurrence_interval,
                    recurrence_days=recurrence_days,
                    date_debut=date_debut,
                    date_fin=date_fin
                )
                recurrent_trajects.append(proposed_traject)
                proposed_traject.save()
                proposed_traject.transport_modes.set(transport_modes)

            # Message de succès après enregistrement
            messages.success(request, 'Proposed Trajects created successfully!')
            return redirect('profile')

        else:
            # Si le formulaire n'est pas valide, afficher les erreurs
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


def generate_recurrent_trajects(traject, proposed_form, user):
    recurrent_trajects = []
    recurrence_type = proposed_form.cleaned_data['recurrence_type']
    recurrence_interval = proposed_form.cleaned_data['recurrence_interval']
    recurrence_days = proposed_form.cleaned_data['recurrence_days']
    date_debut = proposed_form.cleaned_data['date_debut']
    date_fin = proposed_form.cleaned_data['date_fin']

    # Si les dates de début ou fin sont fournies, on les convertit en objets datetime
    if date_debut:
        date_debut = datetime.strptime(str(date_debut), '%Y-%m-%d')
        print("date_debut_recurrent ", str(date_debut))
    if date_fin:
        date_fin = datetime.strptime(str(date_fin), '%Y-%m-%d')
        print("date_fin_recurrent " + str(date_fin))

    # Cas de récurrence hebdomadaire avec intervalle (tous les x jours)
    if recurrence_type == 'weekly_interval':
        # Générer des trajets chaque jour pendant `recurrence_interval` semaines
        current_date = date_debut
        while current_date <= date_fin:
            # Créer une nouvelle instance à chaque itération
            proposed_traject = proposed_form.save(commit=False)
            proposed_traject.member_id = Members.objects.get(memb_user_fk=user).id
            proposed_traject.traject_id = traject.id
            proposed_traject.date = current_date.date()

            # Ajouter à la liste des trajets récurrents
            print("proposed_traject avant", str(proposed_traject))
            recurrent_trajects.append(proposed_traject)

            # Sauvegarder immédiatement si nécessaire
            proposed_traject.save()
            proposed_form.save_m2m()  # Sauvegarde les relations many-to-many
            print("proposed_traject après", str(proposed_traject))

            # Avancer de 1 jour
            current_date += timedelta(days=1)
            print("current_date ", str(current_date))


    # Cas de récurrence sur des jours spécifiques (MO, WE, FR)
    elif recurrence_type == 'specific_days':
        # Convertir les jours spécifiques en une liste de jours de la semaine
        specific_days = [day.strip() for day in recurrence_days.split(',')]
        current_date = date_debut
        while current_date <= date_fin:
            # Si le jour actuel correspond à un des jours spécifiques
            if current_date.strftime('%a').upper() in specific_days:
                proposed_traject = proposed_form.save(commit=False)
                proposed_traject.date = current_date.date()
                recurrent_trajects.append(proposed_traject)
                proposed_traject.save()  # Sauvegarder immédiatement si le jour correspond

            # Avancer d'un jour
            current_date += timedelta(days=1)  # Avancer d'un jour

    return recurrent_trajects
