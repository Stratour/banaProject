from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions
from django.conf import settings
from django.contrib import messages
from .models import Traject, Members, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm
from django.db.models import Q
from datetime import datetime
from django.core.paginator import Paginator


# ====================')= listing ====================')==== #
def all_trajects(request):
    print('============== views :: all_trajects ===================')
    active_tab = request.GET.get('active_tab', 'proposed')
    start_adress = request.GET.get('start_adress', '').strip()
    end_adress = request.GET.get('end_adress', '').strip()
    date_str = request.GET.get('date', '').strip()
    transport_modes = request.GET.getlist('transport_modes') 
    recurrence_type = request.GET.get('recurrence_type', '').strip()
    recurrence_interval = request.GET.get('recurrence_interval', '').strip()
    tr_weekdays = request.GET.getlist('tr_weekdays')
    date_debut_str = request.GET.get('date_debut', '').strip()
    date_fin_str = request.GET.get('date_fin', '').strip()
    
    proposed_trajects_list = ProposedTraject.objects.all().order_by('-departure_time')
    researched_trajects_list = ResearchedTraject.objects.select_related('traject').all().order_by('-departure_time')

    # Filtrage adresse global (query = adresse, ville, CP, etc.)
    if start_adress:
        filters = Q(traject__start_adress__icontains=start_adress) | Q(traject__start_street__icontains=start_adress) | Q(traject__start_locality__icontains=start_adress) | Q(traject__start_cp__icontains=start_adress)
        proposed_trajects_list = proposed_trajects_list.filter(filters)
        researched_trajects_list = proposed_trajects_list.filter(filters)

    if end_adress:
            filters = Q(traject__end_adress__icontains=end_adress) | Q(traject__end_street__icontains=end_adress) | Q(traject__end_locality__icontains=end_adress) | Q(traject__end_cp__icontains=end_adress)
            proposed_trajects_list = proposed_trajects_list.filter(filters)
            researched_trajects_list = researched_trajects_list.filter(filters)
            
    if recurrence_type:
        proposed_trajects_list = proposed_trajects_list.filter(recurrence_type=recurrence_type)

    if recurrence_interval:
        proposed_trajects_list = proposed_trajects_list.filter(recurrence_interval=recurrence_interval)

    if tr_weekdays:
        tr_weekdays = [int(day) for day in tr_weekdays]
        proposed_trajects_list = proposed_trajects_list.filter(date__week_day__in=tr_weekdays)

    # Filtrage par date
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # Format de la date
            proposed_trajects_list = proposed_trajects_list.filter(date=date_obj)
            researched_trajects_list = researched_trajects_list.filter(date=date_obj)
        except ValueError:
            pass  # Si la date est mal formée, on ignore le filtrage

     # --- Si l'utilisateur a choisi une date de début ---
    if date_debut_str:
        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
    
            # Définir les bornes de la semaine (lundi au dimanche)
            start_of_week = date_debut - timedelta(days=date_debut.weekday())   # Lundi
            end_of_week = start_of_week + timedelta(days=6)                     # Dimanche
    
            if tr_weekdays:
                # L'utilisateur a sélectionné des jours précis dans la semaine
                tr_weekdays = [int(day) for day in tr_weekdays]  # ['2', '4'] → [2, 4]
                matched_dates = []
    
                for day in tr_weekdays:
                    offset = (day - 1) % 7  # car lundi = 1 → offset 0, dimanche = 7 → offset 6
                    target_date = start_of_week + timedelta(days=offset)
                    if start_of_week <= target_date <= end_of_week:
                        matched_dates.append(target_date)
    
                # Appliquer le filtre sur les dates trouvées
                proposed_trajects_list = proposed_trajects_list.filter(date__in=matched_dates)
                researched_trajects_list = researched_trajects_list.filter(date__in=matched_dates)
    
            else:
                # Aucun jour précis : on filtre tous les trajets dans cette semaine
                proposed_trajects_list = proposed_trajects_list.filter(date__range=(start_of_week, end_of_week))
                researched_trajects_list = researched_trajects_list.filter(date__range=(start_of_week, end_of_week))
    
        except ValueError:
            pass  # Si date mal formée, on ignore le filtre
    else:
        # Si pas de date_debut => NE RIEN AFFICHER
        proposed_trajects_list = proposed_trajects_list.none()
        researched_trajects_list = researched_trajects_list.none()
        
   # Filtrage par modes de transport
    if transport_modes:
        transport_modes_objs = TransportMode.objects.filter(name__in=transport_modes)
        proposed_trajects_list = proposed_trajects_list.filter(transport_modes__in=transport_modes_objs)
        researched_trajects_list = researched_trajects_list.filter(transport_modes__in=transport_modes_objs)


    # Pagination
    proposed_trajects = Paginator(proposed_trajects_list, 10).get_page(request.GET.get('page1'))
    researched_trajects = Paginator(researched_trajects_list, 10).get_page(request.GET.get('page2'))

    context = {
        'active_tab': active_tab,
        'proposed_trajects': proposed_trajects,
        'researched_trajects': researched_trajects,
        'start_adress': start_adress,
        'end_adress': end_adress,
        'date': date_str,
        'date_debut': date_debut_str,
        'date_fin': date_fin_str,
        'transport_modes': transport_modes,
        'recurrence_type': recurrence_type,
        'recurrence_interval': recurrence_interval,
        'tr_weekdays': request.GET.getlist('tr_weekdays'),
        'days_of_week': [
            ('2', 'Lundi'),
            ('3', 'Mardi'),
            ('4', 'Mercredi'),
            ('5', 'Jeudi'),
            ('6', 'Vendredi'),
            ('7', 'Samedi'),
            ('1', 'Dimanche'),
        ],


    }
    return render(request, 'trajects/trajects_page.html', context)

'''# Filtering based on start and end regions
    if start_region:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__start_region__icontains=start_region)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__start_region__icontains=start_region)
        )

    if end_region:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__end_region__icontains=end_region)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__end_region__icontains=end_region)
        )
    Si une région est sélectionnée, filtrer les trajets en fonction de la région de départ et/ou d’arrivée
    if region:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__start_region__icontains=region) | Q(traject__end_region__icontains=region)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__start_region__icontains=region) | Q(traject__end_region__icontains=region)
        )

    # Filtrer par ville si l'utilisateur entre une ville
    if city_search:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__start_locality__icontains=city_search) | Q(traject__end_locality__icontains=city_search)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__start_locality__icontains=city_search) | Q(traject__end_locality__icontains=city_search)
        )
    # Filtrer par code postal si l'utilisateur entre un code postal
    if postal_code_search:
        proposed_trajects_list = proposed_trajects_list.filter(
            Q(traject__start_cp__icontains=postal_code_search) | Q(
                traject__end_cp__icontains=postal_code_search)
        )
        researched_trajects_list = researched_trajects_list.filter(
            Q(traject__start_cp__icontains=postal_code_search) | Q(
                traject__end_cp__icontains=postal_code_search)
        )'''

def autocomplete_view(request):
    print('=========================================== views :: autocomplete_view ====================')
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


# ====================')= reservation page ====================')==== #
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
    print('=========================================== views :: reserve_traject ====================')
    traject = get_object_or_404(ProposedTraject, id=id)
    is_creator = traject.user == request.user  # Vérifier si l'utilisateur est le créateur du trajet

    # Si l'utilisateur n'est pas le créateur
    if not is_creator:
        print('=========================================== views :: reserve_traject > if not is_creator ==')
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
                    user=request.user,
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
        print('=========================================== views :: reserve_traject > if is_creator ==')
        reservation_requests = Reservation.objects.filter(traject=traject)
        context['reservation_requests'] = reservation_requests
    else:
        reservation_count = Reservation.objects.filter(
            traject=traject).count()  # Remplacer par le nombre réel de réservations
        context['reservation_count'] = reservation_count

    return render(request, 'trajects/reserve_traject.html', context)



@login_required
def reserve_trajectResearched(request, researchedTraject_id):
    print('=========================================== views :: reserve_trajectResearched ====================')
    researched_traject = get_object_or_404(ResearchedTraject, id=researchedTraject_id)
    # Vérifier si un trajet proposé correspondant existe
    try:
        proposed_traject = ProposedTraject.objects.get(traject_id=researched_traject.traject_id)
        print(proposed_traject)

        return reserve_traject(request, proposed_traject.id)  # Appel direct pour éviter la répétition
    except ProposedTraject.DoesNotExist:
        messages.error(request, "Ce trajet n'existe pas encore dans les trajets proposés.")
        return  all_trajects(request)

@login_required
def manage_reservation(request, reservation_id, action):
    print('=========================================== views :: manage_reservation ====================')
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


# ====================')= Utility functions ====================')==== #

def generate_recurrent_trajects(request, recurrent_dates, traject, departure_time, arrival_time,
                                number_of_places, details, recurrence_type, recurrence_interval,
                                recurrence_days, date_debut, date_fin, cleaned_data):
    print('=== views :: generate_recurrent_trajects ===')
    recurrent_trajects = []

    for date in recurrent_dates:
        proposed_traject = ProposedTraject(
            user=request.user,
            traject=traject,
            date=date,
            departure_time=departure_time,
            arrival_time=arrival_time,
            number_of_places=number_of_places,
            details=details,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval if recurrence_type != 'none' else None,
            recurrence_days=recurrence_days,
            date_debut=date_debut if recurrence_type != 'none' else None,
            date_fin=date_fin if recurrence_type != 'none' else None
        )
        proposed_traject.save()
        proposed_traject.transport_modes.set(cleaned_data.get('transport_modes'))
        proposed_traject.languages.set(cleaned_data.get('languages'))
        recurrent_trajects.append(proposed_traject)

    return recurrent_trajects



def handle_form_submission(request, traject_form, proposed_form):
    print('=== views :: handle_form_submission ===')
    if traject_form.is_valid() and proposed_form.is_valid():
        traject = traject_form.save()

        # Données nettoyées
        cleaned_data = proposed_form.cleaned_data
        recurrence_type = cleaned_data.get('recurrence_type')
        recurrence_interval = cleaned_data.get('recurrence_interval')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        selected_days = request.POST.getlist('tr_weekdays')  # ['2', '4']
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        number_of_places = cleaned_data.get('number_of_places')
        details = cleaned_data.get('details')

        # 🟠 Validation minimale
        if not date_debut:
            messages.error(request, "Veuillez choisir une date de départ.")
            return None, False

        if recurrence_type in ['weekly', 'biweekly'] and not date_fin:
            messages.error(request, "Veuillez choisir une date de fin.")
            return None, False

        # 🟢 Pour "une semaine seulement", on considère date_debut == date_fin
        if recurrence_type == 'one_week':
            date_fin = date_debut

        # Générer les dates récurrentes
        recurrent_dates = generate_recurrent_dates(
            date_debut=date_debut,
            date_fin=date_fin,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            specific_days=selected_days
        )

        # Création des objets ProposedTraject
        recurrent_trajects = generate_recurrent_trajects(
            request, recurrent_dates, traject,
            departure_time, arrival_time, number_of_places,
            details, recurrence_type, recurrence_interval,
            recurrence_days, date_debut, date_fin, cleaned_data
        )

        return recurrent_trajects, True

    return None, False



from datetime import timedelta

def generate_recurrent_dates(date_debut, date_fin, recurrence_type, recurrence_interval=None, specific_days=None):
    print('=== views :: generate_recurrent_dates ===')
    recurrent_dates = []

    # Cas 1 : Une seule semaine => générer uniquement les jours choisis dans cette semaine
    if recurrence_type == 'one_week':
        current_date = date_debut
        for i in range(7):  # Parcours les 7 jours de la semaine
            weekday = str((current_date.weekday() + 1))  # Django : Lundi=0 → weekday=1
            if specific_days and weekday in specific_days:
                recurrent_dates.append(current_date)
            current_date += timedelta(days=1)

    # Cas 2 : Toutes les semaines
    elif recurrence_type == 'weekly':
        current_date = date_debut
        while current_date <= date_fin:
            weekday = str((current_date.weekday() + 1))
            if specific_days and weekday in specific_days:
                recurrent_dates.append(current_date)
            current_date += timedelta(days=1)

    # Cas 3 : Une semaine sur deux
    elif recurrence_type == 'biweekly':
        current_date = date_debut
        while current_date <= date_fin:
            # Ajoute les jours spécifiés dans la semaine en cours
            week_start = current_date
            for i in range(7):
                day = week_start + timedelta(days=i)
                weekday = str((day.weekday() + 1))
                if specific_days and weekday in specific_days and day <= date_fin:
                    recurrent_dates.append(day)

            # Sauter une semaine complète
            current_date += timedelta(weeks=2)

    return recurrent_dates



# ====================')= Main view function ====================')==== #


# ====================')= CRUD ====================')==== #

@login_required
def proposed_traject(request, researchesTraject_id=None):
    print('=========================================== views :: proposed_traject ====================')
    researched_traject = None
    traject = None

    # Tentative de récupération des informations de trajet si l'ID est fourni
    if researchesTraject_id:
        try:
            researched_traject = ResearchedTraject.objects.get(id=researchesTraject_id)
            traject = Traject.objects.get(id=researched_traject.traject_id)
        except (ResearchedTraject.DoesNotExist, Traject.DoesNotExist) as e:
            messages.error(request, "Erreur lors de la récupération des trajets.")
            return redirect('accounts:profile')

    # Initialisation des données si `researched_traject` est trouvé
    initial_data = {}
    if researched_traject:
        initial_data = {
            'start_adress': traject.start_adress or f"{traject.start_street}, {traject.start_locality} {traject.start_country}",
            'end_adress': traject.end_adress or f"{traject.end_street}, {traject.end_locality} {traject.end_country}",
            'details': researched_traject.details,
            'number_of_places': researched_traject.number_of_places,
            'departure_time': researched_traject.departure_time,
            'arrival_time': researched_traject.arrival_time,
            'date': researched_traject.date,
            'transport_modes': researched_traject.transport_modes.all(),
        }

    # Traite la soumission du formulaire
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)
        # Vérification des erreurs
        if not traject_form.is_valid():
            print(traject_form.errors)

        if not proposed_form.is_valid():
            print(proposed_form.errors)  # Pour voir les erreurs dans la console du serveur

        recurrent_trajects, success = handle_form_submission(request, traject_form, proposed_form)

        if success:
            messages.success(request, 'Proposed Trajects created successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
    else:
        traject_form = TrajectForm(initial=initial_data)
        proposed_form = ProposedTrajectForm(initial=initial_data)

    # Rendre le contexte pour le template
    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form,
        'researched_traject': researched_traject,
        'days_of_week': [
            ('2', 'Lundi'),
            ('3', 'Mardi'),
            ('4', 'Mercredi'),
            ('5', 'Jeudi'),
            ('6', 'Vendredi'),
            ('7', 'Samedi'),
            ('1', 'Dimanche'),
        ],
    }
    return render(request, 'trajects/proposed_traject.html', context)


@login_required
def searched_traject(request):
    print('=========================================== views :: searched_traject ====================')
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST)
        if traject_form.is_valid() and researched_form.is_valid():
            traject = traject_form.save()
            searched = researched_form.save(commit=False)
            searched.traject = traject
            searched.user = request.user  # Assigner l'utilisateur connecté
            searched.save()
            researched_form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Searched Traject created successfully!')
            return redirect('accounts:profile')
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
    print('=========================================== views :: delete_traject ====================')
    if type == 'proposed':
        traject = get_object_or_404(ProposedTraject, id=id, user=request.user)
    else:
        traject = get_object_or_404(ResearchedTraject, id=id, user=request.user)

    traject.delete()
    messages.success(request, 'Traject deleted successfully!')
    return redirect('profile')


@login_required
def modify_traject(request, id, type):
    print('=========================================== views :: modify_traject ====================')
    if type == 'proposed':
        traject_instance = get_object_or_404(ProposedTraject, id=id, member=request.user.members)
        form_class = ProposedTrajectForm
    else:
        traject_instance = get_object_or_404(ResearchedTraject, id=id, member=request.user.members)
        form_class = ResearchedTrajectForm

    if request.method == 'POST':

        if 'date_debut' in request.POST:
            request.POST = request.POST.copy()  # Rendre mutable
            request.POST['date'] = request.POST['date_debut']  # Copier date_debut vers date

        form = form_class(request.POST, instance=traject_instance)
        form_class.recurrence_type = None

        if form.is_valid():
            form.save()
            messages.success(request, 'Traject updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'There were errors in your form. Please fix them and try again.')
            print(form.errors)  # Debugging des erreurs

    else:
        form = form_class(instance=traject_instance)

    context = {
        'form': form,
        'traject': traject_instance
    }
    return render(request, 'trajects/modify_traject.html', context)
