import re
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions
from django.conf import settings
from django.contrib import messages
from .models import Traject, Members, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm, SimpleProposedTrajectForm
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.utils.timezone import now

def find_matching_trajects(obj):
    """
    Retourne une queryset des trajets compatibles avec l'objet donné (proposé ou recherché),
    en adaptant les filtres selon qu'il s'agit d'un trajet simple ou complet.
    """
    if not isinstance(obj, (ProposedTraject, ResearchedTraject)):
        raise TypeError(f"❌ Objet invalide : {type(obj)} — {obj}")

    time_tolerance = timedelta(minutes=45)
    base_filter = Q()

    # 🎯 Matching depuis un trajet proposé
    if isinstance(obj, ProposedTraject):

        if obj.is_simple:
            print("🔎 Matching depuis un trajet simple proposé")
            
            # Date (obligatoire)
            if obj.date:
                base_filter &= Q(date=obj.date)

            # Start adresse
            if obj.traject and obj.traject.start_adress:
                base_filter &= Q(traject__start_adress__icontains=obj.traject.start_adress.strip())

            # Mode de transport
            if obj.transport_modes.exists():
                base_filter &= Q(transport_modes__in=obj.transport_modes.all())

            return ResearchedTraject.objects.filter(base_filter).distinct()

        else:
            print("🔎 Matching depuis un trajet complet proposé")

            if obj.date:
                base_filter &= Q(date=obj.date)

            if obj.traject and obj.traject.start_adress:
                base_filter &= Q(traject__start_adress__icontains=obj.traject.start_adress.strip())
            if obj.traject and obj.traject.end_adress:
                base_filter &= Q(traject__end_adress__icontains=obj.traject.end_adress.strip())

            if obj.departure_time and obj.departure_time != datetime.strptime("00:00", "%H:%M").time():
                dt = datetime.combine(datetime.today(), obj.departure_time)
                base_filter &= Q(departure_time__range=((dt - time_tolerance).time(), (dt + time_tolerance).time()))

            if obj.arrival_time and obj.arrival_time != datetime.strptime("00:00", "%H:%M").time():
                at = datetime.combine(datetime.today(), obj.arrival_time)
                base_filter &= Q(arrival_time__range=((at - time_tolerance).time(), (at + time_tolerance).time()))

            return ResearchedTraject.objects.filter(base_filter).distinct()

    # 🎯 Matching depuis un trajet recherché
    elif isinstance(obj, ResearchedTraject):
        print("🔎 Matching depuis un trajet recherché (parent)")

        if obj.date:
            base_filter &= Q(date=obj.date)

        if obj.traject and obj.traject.start_adress:
            base_filter &= Q(traject__start_adress__icontains=obj.traject.start_adress.strip())
        if obj.traject and obj.traject.end_adress:
            base_filter &= Q(traject__end_adress__icontains=obj.traject.end_adress.strip())

        if obj.departure_time and obj.departure_time != datetime.strptime("00:00", "%H:%M").time():
            dt = datetime.combine(datetime.today(), obj.departure_time)
            base_filter &= Q(departure_time__range=((dt - time_tolerance).time(), (dt + time_tolerance).time()))

        if obj.arrival_time and obj.arrival_time != datetime.strptime("00:00", "%H:%M").time():
            at = datetime.combine(datetime.today(), obj.arrival_time)
            base_filter &= Q(arrival_time__range=((at - time_tolerance).time(), (at + time_tolerance).time()))

        return ProposedTraject.objects.filter(base_filter).distinct()

    return ProposedTraject.objects.none()
    
@login_required
def my_matchings_researched(request):
    user = request.user
    matches = []

    researched_matches = ResearchedTraject.objects.filter(user=user)
    for research in researched_matches:
        matched = find_matching_trajects(research)
        if matched.exists():
            matches.append({'research': research, 'proposals': matched})

    return render(request, 'trajects/my_matchings_researched.html', {'matches': matches})


@login_required
def my_matchings_proposed(request):
    matches = []
    proposed_matches = ProposedTraject.objects.filter(user=request.user)
    for proposed in proposed_matches:
        print("🧪 TYPE DE proposed =", proposed, type(proposed))
        matched = find_matching_trajects(proposed)
        assert not callable(proposed), "🚨 ERREUR : variable 'proposed' contient une fonction"

        if matched.exists():
            matches.append({'proposal': proposed, 'requests': matched})

    return render(request, 'trajects/my_matchings_proposed.html', {'matches': matches})

def generate_recurrent_dates(date_debut, date_fin, recurrence_type, recurrence_interval=None, specific_days=None):
    """
    Crée une liste de dates valides selon la récurrence.
    - specific_days: liste de strings (ex: ['1', '2']) où 1 = lundi, 7 = dimanche
    """
    recurrent_dates = []

    corrected_days = [int(day) for day in specific_days] if specific_days else None

    if recurrence_type == 'one_week':
        current_date = date_debut - timedelta(days=date_debut.weekday())
        for i in range(7):
            current = current_date + timedelta(days=i)
            weekday = current_date.weekday() + 1  # Lundi = 1, ..., Dimanche = 7
            if corrected_days is None or weekday in corrected_days:
                recurrent_dates.append(current_date)
            current_date += timedelta(days=1)

    elif recurrence_type == 'weekly':
        current_date = date_debut
        while current_date <= date_fin:
            for i in range(7):
                day = current_date + timedelta(days=i)
                if day > date_fin:
                    break
                weekday = day.weekday() + 1
                if corrected_days is None or weekday in corrected_days:
                    recurrent_dates.append(day)
            current_date += timedelta(weeks=1)

    elif recurrence_type == 'biweekly':
        current_date = date_debut
        while current_date <= date_fin:
            for i in range(7):
                day = current_date + timedelta(days=i)
                if day > date_fin:
                    break
                weekday = day.weekday() + 1
                if corrected_days is None or weekday in corrected_days:
                    recurrent_dates.append(day)
            current_date += timedelta(weeks=2)

    return recurrent_dates


# ===================================================
#               🚗 TRAJET PROPOSÉ (YAYA)
# ===================================================

@login_required
def proposed_traject(request, researchesTraject_id=None):
    """
    Vue pour proposer un trajet (yaya).
    Si le formulaire est soumis : enregistre le trajet proposé (1 ou plusieurs selon la récurrence).
    Sinon : affiche le formulaire vide.
    """
    
    ## Préremplissage si une demande parent est liée
    #initial_data = {}
    #if researchesTraject_id:
    #   try:
    #        researched = ResearchedTraject.objects.get(id=researchesTraject_id)
    #        traject = researched.traject
    #        initial_data = {
    #            'start_adress': traject.start_adress,
    #            'end_adress': traject.end_adress,
    #            'details': researched.details,
    #            'number_of_places': researched.number_of_places,
    #            'departure_time': researched.departure_time,
    #            'arrival_time': researched.arrival_time,
    #            'date': researched.date,
    #            'transport_modes': researched.transport_modes.all(),
    #        }
    #    except (ResearchedTraject.DoesNotExist, Traject.DoesNotExist):
    #        messages.error(request, "Erreur lors de la récupération de la demande.")
    #        return redirect('accounts:profile')
    #

    # Soumission du formulaire
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)
        proposed_trajects, success = save_proposed_traject(request, traject_form, proposed_form)
        
        if success:
            for proposed in proposed_trajects:
                matches = find_matching_trajects(proposed)
                if matches.exists():
                    messages.success(request, "Un ou des matchings ont été trouvés. Attendez la demande du parent")
                    return redirect('my_matchings_proposed')
                else:
                    messages.warning(request, "Aucun matching trouvé, votre proposition a été enregistrée.")
            return redirect('my_proposed_trajects')
                    
        else:
            messages.error(request, "Erreur lors de la création du/des trajet(s)")

    else:
        # Affichage initial
        traject_form = TrajectForm()
        proposed_form = ProposedTrajectForm()

    # Rendre le contexte pour le template
    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form,
        'researched_traject': researchesTraject_id,
        'days_of_week': [
            ('1', 'Lundi'),
            ('2', 'Mardi'),
            ('3', 'Mercredi'),
            ('4', 'Jeudi'),
            ('5', 'Vendredi'),
            ('6', 'Samedi'),
            ('7', 'Dimanche'),
        ],
    }
    return render(request, 'trajects/proposed_traject.html', context)

@login_required
def simple_proposed_traject(request):
    """
    Vue pour gérer une proposition rapide d’un trajet (simplifiée pour les yayas).
    """
    if request.method == 'POST':
        form = SimpleProposedTrajectForm(request.POST)

        if form.is_valid():
            user = request.user
            start_adress = form.cleaned_data['start_adress']
            transport_modes = form.cleaned_data['transport_modes']
            weekdays = form.cleaned_data['tr_weekdays']
            date_debut = form.cleaned_data['date_debut']

            traject = Traject.objects.create(
                start_adress=start_adress,
                end_adress="",  # volontairement vide
            )

            matched_any = False
            created_count = 0

            for weekday in weekdays:
                day_offset = (int(weekday) - date_debut.isoweekday()) % 7
                date = date_debut + timedelta(days=day_offset)

                proposed = ProposedTraject.objects.create(
                    user=user,
                    traject=traject,
                    date=date,
                    recurrence_type='one_week',
                    is_simple=True,
                )
                proposed.transport_modes.set(transport_modes)

                # 🔁 MATCHING automatique
                matches = find_matching_trajects(proposed)
                if matches.exists():
                    matched_any = True

                created_count += 1

            if matched_any:
                messages.success(request, f"{created_count} proposition(s) enregistrée(s) avec des correspondances trouvées.")
                return redirect('my_matchings_proposed')
            else:
                messages.warning(request, f"{created_count} proposition(s) enregistrée(s), mais aucun matching trouvé.")
                return redirect('my_proposed_trajects')

        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = SimpleProposedTrajectForm()

    return render(request, 'trajects/simple_proposed_traject.html', {
        'form': form
    })

def save_proposed_traject(request, traject_form, proposed_form):
    """
    Enregistre un ou plusieurs ProposedTrajects avec récurrence (pour les yayas).
    Cette fonction :
    - vérifie la validité des formulaires
    - sauvegarde le Traject de base
    - génère les dates de récurrence
    - crée 1 ou plusieurs ProposedTraject liés à l'utilisateur
    """
    if traject_form.is_valid() and proposed_form.is_valid():
        traject = traject_form.save(commit=False)
        traject.save()

        
        cleaned_data = proposed_form.cleaned_data

        # Récupération des champs
        recurrence_type = cleaned_data.get('recurrence_type')
        recurrence_interval = cleaned_data.get('recurrence_interval')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin') or date_debut  # fallback
        selected_days = request.POST.getlist('tr_weekdays')
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        number_of_places = cleaned_data.get('number_of_places')
        details = cleaned_data.get('details')

        # Validation manuelle de base
        if not date_debut:
            messages.error(request, "Veuillez choisir une date de début.")
            return None, False

        if recurrence_type in ['weekly', 'biweekly'] and not date_fin:
            messages.error(request, "Veuillez choisir une date de fin.")
            return None, False

        # Génération des dates à créer
        recurrent_dates = generate_recurrent_dates(
            date_debut=date_debut,
            date_fin=date_fin,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            specific_days=selected_days
        )

        # Création des ProposedTrajects
        proposed_trajects = generate_recurrent_trajects(
            request=request,
            recurrent_dates=recurrent_dates,
            traject=traject,
            departure_time=departure_time,
            arrival_time=arrival_time,
            number_of_places=number_of_places,
            details=details,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            cleaned_data=cleaned_data
        )

        return proposed_trajects, True        

    return None, False

def generate_recurrent_trajects(request, recurrent_dates, traject, departure_time, arrival_time,
                                number_of_places, details, recurrence_type, recurrence_interval,
                                recurrence_days, date_debut, date_fin, cleaned_data):
    
    proposed_trajects = []
    for date in recurrent_dates:
        proposed = ProposedTraject(
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
        proposed.save()
        proposed.transport_modes.set(cleaned_data.get('transport_modes'))
        proposed.languages.set(cleaned_data.get('languages'))
        proposed_trajects.append(proposed)

    return proposed_trajects

@login_required
def my_proposed_trajects(request):
    user_trajects = ProposedTraject.objects.filter(user=request.user).order_by('date', 'departure_time')
    return render(request, 'trajects/my_proposed_trajects.html', {
        'proposed_trajects': user_trajects
    })
# ===================================================
#               🚗 TRAJET RECHERCHÉ (PARENT)
# ===================================================

@login_required
def researched_traject(request):
    """
    Vue pour qu’un parent enregistre une recherche de trajet.
    - Si POST : enregistre le trajet recherché.
    - Sinon : affiche un formulaire vide.
    """
    transport_modes = TransportMode.objects.all()
    service = request.user.profile.service if hasattr(request.user, 'profile') else None

    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST)
        researched_trajects, success = save_researched_traject(request, traject_form, researched_form)
        
        if success:
            for researched in researched_trajects:
                matches = find_matching_trajects(researched)
                if matches.exists():
                    messages.success(request, "Un ou des matchings ont été trouvés. Faites votre choix")
                    return redirect('my_matchings_researched')
                else:
                    messages.warning(request, "Aucun matching trouvé. Votre demande a été enregistrée.")
            return redirect('my_researched_trajects')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")

            context = {
                'traject_form': traject_form,
                'researched_form': researched_form,
                'transport_modes': transport_modes,
                'days_of_week': [
                    ('1', 'Lundi'),
                    ('2', 'Mardi'),
                    ('3', 'Mercredi'),
                    ('4', 'Jeudi'),
                    ('5', 'Vendredi'),
                    ('6', 'Samedi'),
                    ('7', 'Dimanche'),
                ],
                # Champs personnalisés à préremplir
                'start_adress': request.POST.get('start_adress', ''),
                'end_adress': request.POST.get('end_adress', ''),
                'departure_time': request.POST.get('departure_time', ''),
                'arrival_time': request.POST.get('arrival_time', ''),
                'recurrence_type': request.POST.get('recurrence_type', ''),
                'tr_weekdays': request.POST.getlist('tr_weekdays'),
                'date_debut': request.POST.get('date_debut', ''),
                'date_fin': request.POST.get('date_fin', ''),
            }
            return render(request, 'trajects/searched_traject.html', context)
    else:
        traject_form = TrajectForm()
        researched_form = ResearchedTrajectForm()

        context = {
            'traject_form': traject_form,
            'researched_form': researched_form,
            'transport_modes': transport_modes,
            'days_of_week': [
                ('1', 'Lundi'),
                ('2', 'Mardi'),
                ('3', 'Mercredi'),
                ('4', 'Jeudi'),
                ('5', 'Vendredi'),
                ('6', 'Samedi'),
                ('7', 'Dimanche'),
            ],
            'service': service,
        }
    return render(request, 'trajects/searched_traject.html', context)

def save_researched_traject(request, traject_form, researched_form):
    """
    Enregistre un ResearchedTraject (demande parent).
    Cette fonction :
    - vérifie la validité des formulaires
    - sauvegarde le Traject de base
    - lie le ResearchedTraject à l’utilisateur courant
    """
    if traject_form.is_valid() and researched_form.is_valid():
        traject = traject_form.save(commit=False)
        traject.save()

        cleaned_data = researched_form.cleaned_data
        
        recurrence_type = cleaned_data.get('recurrence_type')
        recurrence_interval = cleaned_data.get('recurrence_interval')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin') or date_debut
        selected_days = request.POST.getlist('tr_weekdays')
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        
        if not date_debut:
            messages.error(request, "Veuillez choisir une date de début.")
            return None, False

        if recurrence_type in ['weekly', 'biweekly'] and not date_fin:
            messages.error(request, "Veuillez choisir une date de fin.")
            return None, False
        
        recurrent_dates = generate_recurrent_dates(
            date_debut=date_debut,
            date_fin=date_fin,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            specific_days=selected_days
        )

        researched_trajects = generate_recurrent_researches(
            request=request,
            recurrent_dates=recurrent_dates,
            traject=traject,
            departure_time=departure_time,
            arrival_time=arrival_time,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            cleaned_data=cleaned_data
        )

        return researched_trajects, True

    return None, False

def generate_recurrent_researches(request, recurrent_dates, traject,
                                  departure_time, arrival_time,
                                  recurrence_type, recurrence_interval,
                                  recurrence_days, date_debut, date_fin,
                                  cleaned_data):
    recurrent_researches = []
    for date in recurrent_dates:
        researched = ResearchedTraject(
            user=request.user,
            traject=traject,
            date=date,
            departure_time=departure_time,
            arrival_time=arrival_time,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval if recurrence_type != 'none' else None,
            recurrence_days=recurrence_days,
            date_debut=date_debut if recurrence_type != 'none' else None,
            date_fin=date_fin if recurrence_type != 'none' else None
        )
        researched.save()
        researched.transport_modes.set(cleaned_data.get('transport_modes'))
        recurrent_researches.append(researched)
    return recurrent_researches

@login_required
def my_researched_trajects(request):
    user_trajects = ResearchedTraject.objects.filter(user=request.user).order_by('date', 'departure_time')
    return render(request, 'trajects/my_researched_trajects.html', {
        'researched_trajects': user_trajects
        
    })

@login_required
def all_proposed_trajects(request):
    proposed_trajects = ProposedTraject.objects.select_related('traject', 'user')
    return render(request, 'trajects/all_proposed_trajects.html', {
        'proposed_trajects': proposed_trajects
    })

@login_required
def all_researched_trajects(request):
    researched_trajects = ResearchedTraject.objects.select_related('traject', 'user')
    return render(request, 'trajects/all_researched_trajects.html', {
        'researched_trajects': researched_trajects
    })


@login_required
def delete_proposed_traject(request, pk):
    trajet = get_object_or_404(ProposedTraject, pk=pk, user=request.user)
    trajet.delete()
    messages.success(request, "Le trajet proposé a été supprimé.")
    return redirect('my_proposed_trajects')

@login_required
def delete_researched_traject(request, pk):
    trajet = get_object_or_404(ResearchedTraject, pk=pk, user=request.user)
    trajet.delete()
    messages.success(request, "Le trajet recherché a été supprimé.")
    return redirect('my_researched_trajects')


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



#@login_required
#def reserve_trajectResearched(request, researchedTraject_id):
#    researched_traject = get_object_or_404(ResearchedTraject, id=researchedTraject_id)
#    # Vérifier si un trajet proposé correspondant existe
#    try:
#        proposed_traject = ProposedTraject.objects.get(traject_id=researched_traject.traject_id)
#        print(proposed_traject)
#
#        return reserve_traject(request, proposed_traject.id)  # Appel direct pour éviter la répétition
#    except ProposedTraject.DoesNotExist:
#        messages.error(request, "Ce trajet n'existe pas encore dans les trajets proposés.")
#        return  all_trajects(request)

@login_required
def manage_reservation(request, reservation_id, action):
    # Récupérer la réservation
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Vérifier que l'utilisateur est bien le yaya (propriétaire du trajet)
    if reservation.traject.user != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette réservation.")
        return redirect('my_reservations')

    # Vérifier si déjà traitée
    if reservation.status != 'pending':
        messages.warning(request, "Cette réservation a déjà été traitée.")
        return redirect('my_reservations')

    if action == 'accept':
        available_places = int(reservation.traject.number_of_places)
        requested_places = reservation.number_of_places

        if requested_places > available_places:
            messages.error(request, "Pas assez de places disponibles.")
        else:
            # Confirmer la réservation
            reservation.status = 'confirmed'
            reservation.save()

            # Mettre à jour les places restantes
            reservation.traject.number_of_places = str(available_places - requested_places)
            reservation.traject.save()

            # Supprimer le trajet s’il n’y a plus de places
            if int(reservation.traject.number_of_places) <= 0:
                reservation.traject.delete()

            messages.success(request, "Réservation confirmée.")
    
    elif action == 'reject':
        reservation.status = 'canceled'
        reservation.save()
        messages.success(request, "Réservation refusée.")

    else:
        messages.error(request, "Action invalide.")

    return redirect('my_reservations')



@login_required
def auto_reserve(request, proposed_id):
    traject = get_object_or_404(ProposedTraject, id=proposed_id)

    if traject.user == request.user:
        messages.error(request, "Vous ne pouvez pas réserver votre propre trajet.")
        return redirect('my_matchings_researched')

    requested_places = 1
    available_places = int(traject.number_of_places)

    if requested_places > available_places:
        messages.error(request, "Plus assez de places disponibles.")
        return redirect('my_matchings_researched')

    Reservation.objects.create(
        user=request.user,
        traject=traject,
        number_of_places=requested_places,
        status='pending',
        reservation_date=now()
    )

    traject.number_of_places = str(available_places - requested_places)
    traject.save()

    if int(traject.number_of_places) <= 0:
        traject.is_active = False
        traject.save()

    date_str = now().strftime("%d/%m/%Y à %H:%M")

    #send_mail(
    #    subject="Réservation confirmée",
    #    message=f"Réservation prise le {date_str} avec '{traject.user.username}'.",
    #    from_email=settings.DEFAULT_FROM_EMAIL,
    #    recipient_list=[request.user.email],
    #)
#
    #send_mail(
    #    subject="Nouvelle réservation reçue",
    #    message=f"Une réservation a été effectuée par '{request.user.username}' le {date_str}.",
    #    from_email=settings.DEFAULT_FROM_EMAIL,
    #    recipient_list=[traject.user.email],
    #)

    messages.success(request, "Réservation confirmée.")
    return redirect('my_reservations')

@login_required
def my_reservations(request):
    user = request.user

    # En tant que parent (réservations faites)
    made_reservations = Reservation.objects.filter(user=user).select_related('traject', 'traject__traject')

    # En tant que yaya (réservations reçues sur mes trajets)
    received_reservations = Reservation.objects.filter(traject__user=user).select_related('user', 'traject', 'traject__traject')

    return render(request, 'trajects/my_reservations.html', {
        'made_reservations': made_reservations,
        'received_reservations': received_reservations,
    })