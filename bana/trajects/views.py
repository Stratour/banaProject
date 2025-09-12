import re
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions
from django.conf import settings
from django.contrib import messages
from accounts.models import Child
from stripe_sub.models import Subscription
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm, SimpleProposedTrajectForm, ResearchedTrajectForm
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import date

def find_matching_trajects(obj):
    """
    Fonction universelle de matching SYMÉTRIQUE sur les adresses de départ/arrivée.
    - Marche pour une proposition classique, proposition simple, ou recherche parent.
    - Matching dans les deux sens : 'a contient b' ou 'b contient a'.
    """

    # Tolérance sur l'heure (± 45 minutes)
    time_tolerance = timedelta(minutes=45)
    results = set()  # Utilisé pour éviter les doublons dans les résultats

    def normalize(ad):
        """
        Normalise une adresse pour comparaison : minuscule, espaces supprimés.
        """
        return ad.strip().lower() if ad else ''

    # ============================
    # 1. Cas où obj = ResearchedTraject (un parent recherche un trajet)
    # ============================
    if isinstance(obj, ResearchedTraject):

        # --- SENS 1 : On récupère toutes les propositions qui CONTIENNENT l'adresse recherchée ---
        qs1 = ProposedTraject.objects.filter(date=obj.date, date_debut__gte=date.today())
        if obj.traject and obj.traject.start_adress:
            qs1 = qs1.filter(traject__start_adress__icontains=obj.traject.start_adress.strip())
        if obj.traject and obj.traject.end_adress:
            qs1 = qs1.filter(traject__end_adress__icontains=obj.traject.end_adress.strip())
        if obj.departure_time:
            dt = datetime.combine(datetime.today(), obj.departure_time)
            qs1 = qs1.filter(departure_time__range=((dt - time_tolerance).time(), (dt + time_tolerance).time()))
        if obj.arrival_time:
            at = datetime.combine(datetime.today(), obj.arrival_time)
            qs1 = qs1.filter(arrival_time__range=((at - time_tolerance).time(), (at + time_tolerance).time()))
        results.update(list(qs1))  # On ajoute les résultats au set

        # --- SENS 2 : On récupère toutes les propositions, puis on garde celles où L'ADRESSE DU PROPOSÉ contient l'adresse recherchée ---
        all_proposed = ProposedTraject.objects.filter(date=obj.date, date_debut__gte=date.today())
        for proposed in all_proposed:
            parent_dep = normalize(obj.traject.start_adress if obj.traject else '')
            prop_dep = normalize(proposed.traject.start_adress if proposed.traject else '')
            parent_arr = normalize(obj.traject.end_adress if obj.traject else '')
            prop_arr = normalize(proposed.traject.end_adress if proposed.traject else '')

            # Test symétrique dans les deux sens (adresse de départ et d'arrivée)
            match_dep = (parent_dep in prop_dep or prop_dep in parent_dep) if parent_dep and prop_dep else True
            match_arr = (parent_arr in prop_arr or prop_arr in parent_arr) if parent_arr and prop_arr else True

            # Debug pour voir exactement ce qui matche ou non
            print(f"[MATCHING][parent] dep:'{parent_dep}' <-> '{prop_dep}' => {match_dep} | arr:'{parent_arr}' <-> '{prop_arr}' => {match_arr}")

            # Si départ ET arrivée matche, on garde la proposition
            if match_dep and match_arr:
                results.add(proposed)

        return list(results)

    # ============================
    # 2. Cas où obj = ProposedTraject (un yaya ou parent propose un trajet)
    # ============================
    elif isinstance(obj, ProposedTraject):

        # --- SENS 1 : On récupère toutes les recherches qui CONTIENNENT l'adresse proposée ---
        qs1 = ResearchedTraject.objects.filter(date=obj.date, date_debut__gte=date.today())
        if obj.traject and obj.traject.start_adress:
            qs1 = qs1.filter(traject__start_adress__icontains=obj.traject.start_adress.strip())
        if obj.traject and obj.traject.end_adress:
            qs1 = qs1.filter(traject__end_adress__icontains=obj.traject.end_adress.strip())
        if obj.departure_time:
            dt = datetime.combine(datetime.today(), obj.departure_time)
            qs1 = qs1.filter(departure_time__range=((dt - time_tolerance).time(), (dt + time_tolerance).time()))
        if obj.arrival_time:
            at = datetime.combine(datetime.today(), obj.arrival_time)
            qs1 = qs1.filter(arrival_time__range=((at - time_tolerance).time(), (at + time_tolerance).time()))
        results.update(list(qs1))

        # --- SENS 2 : On récupère toutes les recherches, puis on garde celles où l'adresse proposée contient la recherche ---
        all_researched = ResearchedTraject.objects.filter(date=obj.date, date_debut__gte=date.today())
        for researched in all_researched:
            yaya_dep = normalize(obj.traject.start_adress if obj.traject else '')
            req_dep = normalize(researched.traject.start_adress if researched.traject else '')
            yaya_arr = normalize(obj.traject.end_adress if obj.traject else '')
            req_arr = normalize(researched.traject.end_adress if researched.traject else '')

            match_dep = (yaya_dep in req_dep or req_dep in yaya_dep) if yaya_dep and req_dep else True
            match_arr = (yaya_arr in req_arr or req_arr in yaya_arr) if yaya_arr and req_arr else True

            # Debug
            print(f"[MATCHING][proposed] dep:'{yaya_dep}' <-> '{req_dep}' => {match_dep} | arr:'{yaya_arr}' <-> '{req_arr}' => {match_arr}")

            if match_dep and match_arr:
                results.add(researched)

        return list(results)

    # Si obj n'est ni une recherche ni une proposition, on retourne une liste vide
    return []

@login_required
def my_matchings_researched(request):
    '''PArent recherche'''
    user = request.user
    matches = []

    researched_matches = ResearchedTraject.objects.filter(user=user, is_active=True, date__gte=date.today())
    is_abonned = Subscription.is_user_abonned(user)
    print('============ TRAJECTS > my_matchings_researched > is_abonned :: ', is_abonned)

    print('============== parent :: my_matchings_researched :: researched_matches', len(researched_matches))
    for research in researched_matches:
        matched = find_matching_trajects(research)
        print('for parent', len(matched))
        if matched:
            print('matched parent ok')
            matches.append({'research': research, 'proposals': matched})
    
    return render(request, 'trajects/my_matchings_researched.html', {'matches': matches, 'is_abonned': is_abonned})


@login_required
def my_matchings_proposed(request):
    '''yaya/parent recherche'''
    user = request.user
    matches = []
    proposed_matches = ProposedTraject.objects.filter(user=request.user, is_active=True, date__gte=date.today())
    is_abonned = Subscription.is_user_abonned(user)
    print('============== yaya :: my_matchings_proposed :: proposed_matches', len(proposed_matches))
    for proposed in proposed_matches:
        matched = find_matching_trajects(proposed)
        print('for yaya')
        if matched:
            print('matched yaya ok')
            matches.append({'proposal': proposed, 'requests': matched})

    return render(request, 'trajects/my_matchings_proposed.html', {'matches': matches, 'is_abonned': is_abonned})

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
            matched_any = False
            created_count = 0
            total_matches = 0
            
            for proposed in proposed_trajects:
                matches = find_matching_trajects(proposed)
                match_count = len(matches)
                if match_count > 0:
                    matched_any = True
                    total_matches += match_count
                created_count += 1
                
            if matched_any:
                messages.success(
                    request,
                    f"{created_count} proposition(s) enregistrée(s) avec {total_matches} matching(s) trouvés."
                )
                return redirect('my_matchings_proposed')
            else:
                messages.warning(
                    request,
                    f"{created_count} proposition(s) enregistrée(s), mais aucun matching trouvé."
                )
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

    if request.method == 'POST':
        form = SimpleProposedTrajectForm(request.POST)

        if form.is_valid():
            user = request.user
            start_adress = form.cleaned_data['start_adress']
            transport_modes = form.cleaned_data['transport_modes']
            weekdays = form.cleaned_data['tr_weekdays']
            date_debut = form.cleaned_data['date_debut']
            number_of_places = form.cleaned_data['number_of_places']

            traject = Traject.objects.create(
                start_adress=start_adress,
                end_adress="",
            )

            matched_any = False
            created_count = 0
            total_matches = 0  # compteur pour tous les matchings

            for weekday in weekdays:
                day_offset = (int(weekday) - date_debut.isoweekday()) % 7
                date = date_debut + timedelta(days=day_offset)

                proposed = ProposedTraject.objects.create(
                    user=user,
                    traject=traject,
                    date=date,
                    recurrence_type='one_week',
                    is_simple=True,
                    number_of_places=number_of_places
                )
                proposed.transport_modes.set(transport_modes)

                # 🔁 MATCHING automatique
                matches = find_matching_trajects(proposed)
                match_count = len(matches)
                if match_count > 0:
                    matched_any = True
                    total_matches += match_count

                created_count += 1

            if matched_any:
                messages.success(request, f"{created_count} proposition(s) enregistrée(s) avec {total_matches} matching(s) trouvés.")
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
    user_trajects = ProposedTraject.objects.filter(user=request.user, is_active=True, date__gte=date.today()).order_by('date', 'departure_time')
    # La requete qui suit affiche tous les enregistrements dont la date de départ est indérieure à la date d'aujourd'hui
    #user_past_trajects = ProposedTraject.objects.filter(user=request.user, is_active=True, date_debut__lt=date.today()).order_by('date', 'departure_time')
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
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)
        researched_trajects, success = save_researched_traject(request, traject_form, researched_form)
        
        if success:
            matched_any = False
            created_count = 0
            total_matches = 0 
            
            for researched in researched_trajects:
                matches = find_matching_trajects(researched)
                match_count = len(matches)
                if match_count > 0:
                    matched_any = True
                    total_matches += match_count
                created_count += 1
                
            if matched_any:
                messages.success(
                    request,
                    f"{created_count} recherche(s) enregistrée(s) avec {total_matches} matching(s) trouvés."
                )
                return redirect('my_matchings_researched')
            else:
                messages.warning(
                    request,
                    f"{created_count} recherche(s) enregistrée(s), mais aucun matching trouvé."
                )
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
        username = request.user.username
        print("=============== request.user.username :: ", username)
        traject_form = TrajectForm()
        researched_form = ResearchedTrajectForm(user=request.user)

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
        researched.children.set(cleaned_data.get('children'))

        r = ResearchedTraject.objects.last()
        print(r.children.all())  # ➜ doit afficher une queryset non vide
        recurrent_researches.append(researched)
    return recurrent_researches

@login_required
def my_researched_trajects(request):
    user_trajects = ResearchedTraject.objects.filter(user=request.user, is_active=True, date__gte=date.today()).order_by('date', 'departure_time')
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


'''@login_required
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
'''
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
        requested_places = reservation.number_of_places
        available_places = reservation.traject.number_of_places
        
        if requested_places > available_places:
            messages.error(request, "Il n'y a plus assez de places disponibles.")
            return redirect('my_reservations')
        
        reservation.status = 'confirmed'
        reservation.save()

         # ✅ Envoi d'un email de confirmation au parent
        parent_email = reservation.user.email
        yaya_name = request.user.profile.verified_first_name
        trajet_info = f"{reservation.traject.traject.start_adress} → {reservation.traject.traject.end_adress}"
        nb_enfants = reservation.number_of_places

        send_mail(
            subject="Votre réservation a été confirmée sur Bana",
            message=(
                f"Bonjour {reservation.user.profile.verified_first_name},\n\n"
                f"Votre demande de réservation pour le trajet {trajet_info} "
                f"({nb_enfants} enfant(s)) a été confirmée par {yaya_name}.\n\n"
                "Connectez-vous à Bana pour plus d'informations. http://www.bana.mobi/trajects/my_reserve/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False,
        )
        reservation.traject.number_of_places -= requested_places
        reservation.traject.save()
        
        # ✅ Désactiver le trajet si complet
        if reservation.traject.number_of_places <= 0:
            reservation.traject.is_active = False
            reservation.traject.save()
                    
        messages.success(request, "Réservation confirmée.")

    elif action == 'reject':
        reservation.status = 'canceled'
        reservation.save()

        parent_email = reservation.user.email
        yaya_name = request.user.profile.verified_first_name
        trajet_info = f"{reservation.traject.traject.start_adress} → {reservation.traject.traject.end_adress}"
        nb_enfants = reservation.number_of_places

        send_mail(
            subject="Votre réservation a été refusée ou le trajet n'est plus disponible",
            message=(
                f"Bonjour {reservation.user.profile.verified_first_name},\n\n"
                f"Nous sommes désolés, mais votre demande de réservation pour le trajet {trajet_info} "
                f"({nb_enfants} enfant(s)) a été déclinée ou le trajet n'est plus disponible.\n\n"
                "N'hésitez pas à rechercher un autre accompagnateur sur Bana."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False,
        )
        messages.success(request, "Réservation refusée.")

    else:
        messages.error(request, "Action invalide.")

    return redirect('my_reservations')



@login_required
def auto_reserve(request, proposed_id, researched_id):
    traject = get_object_or_404(ProposedTraject, id=proposed_id)

    if traject.user == request.user:
        messages.error(request, "Vous ne pouvez pas réserver votre propre trajet.")
        return redirect('my_matchings_researched')

    # ✅ On récupère précisément la demande faite par ce parent
    researched = get_object_or_404(ResearchedTraject, id=researched_id, user=request.user)

    # ✅ Nombre d'enfants sélectionnés = nombre de places à réserver
    requested_places = researched.children.count()

    # ✅ Création de la réservation
    reservation = Reservation.objects.create(
        user=request.user,
        traject=traject,
        number_of_places=requested_places,
        status='pending',
        reservation_date=now()
    )
    
    reservation.transport_modes.set(researched.transport_modes.all())

    # ✅ Optionnel : lier les enfants à la réservation (si tu ajoutes reservation.children)
    # reservation.children.set(researched.children.all())

    # --- Envoi d'un email au yaya ---
    proposer_email = traject.user.email
    parent_name = request.user.profile.verified_first_name
    trajet_info = f"{traject.traject.start_adress} → {traject.traject.end_adress}"
    nb_enfants = requested_places

    send_mail(
        subject="Nouvelle demande de réservation reçue sur Bana",
        message=(
            f"Bonjour {traject.user.profile.verified_first_name},\n\n"
            f"Vous avez reçu une nouvelle demande de réservation de la part de {parent_name}.\n\n"
            f"Détails du trajet : {trajet_info}\n"
            f"Nombre d'enfant(s) demandé(s) : {nb_enfants}\n\n"
            "Connectez-vous à Bana pour accepter ou refuser la demande."
            "http://www.bana.mobi/trajects/my_reserve/"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[proposer_email],
        fail_silently=False,
    )
    
    messages.success(request, "Votre demande de réservation a été envoyée.")
    return redirect('my_reservations')

@login_required
def propose_help(request, researched_id):
    research = get_object_or_404(ResearchedTraject, id=researched_id)

    #Vérification pour éviter les notifications multiples
    session_key = f"help_notified_{request.user.id}_{researched_id}"
    
    if request.session.get(session_key, False):
        messages.info(request, "Vous avez déjà signalé votre disponibilité pour ce trajet.")
        return redirect('my_matchings_proposed')

    # Marquer comme notifié dans cette session
    request.session[session_key] = True
    
    # Tu peux ici créer une vraie liaison si tu as un modèle intermédiaire "HelpRequest" ou autre

    # Envoi du mail au parent
    parent_email = research.user.email
    yaya_name = request.user.profile.verified_first_name
    trajet_info = f"{research.traject.start_adress} → {research.traject.end_adress}"
    date_str = research.date.strftime("%d/%m/%Y") if research.date else ""
    heure_depart = research.departure_time.strftime("%H:%M") if research.departure_time else "—"

    send_mail(
        subject="Un accompagnateur a répondu à votre recherche de trajet",
        message=(
            f"Bonjour {research.user.profile.verified_first_name},\n\n"
            f"Bonne nouvelle ! Un accompagnateur est disponible pour votre recherche de trajet :\n\n"
            f"{trajet_info} le {date_str} (départ à {heure_depart}).\n\n"
            "Connectez-vous à Bana pour consulter cette proposition et valider votre réservation."
            "https://www.bana.mobi/trajects/matchings/yaya/"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[parent_email],
        fail_silently=False,
    )

    messages.success(request, "Votre aide a été proposée et le parent a été informé par email.")
    return redirect('my_matchings_proposed')  # ou la page de ton choix

@login_required
def my_reservations(request):
    user = request.user

    # Vérifier si l'utilisateur a un abonnement actif
    is_abonned = Subscription.is_user_abonned(user)

    # En tant que parent (réservations faites)
    made_reservations = Reservation.objects.filter(user=user).select_related('traject', 'traject__traject')

    # En tant que yaya (réservations reçues sur mes trajets)
    received_reservations = Reservation.objects.filter(traject__user=user).select_related('user', 'traject', 'traject__traject')

    return render(request, 'trajects/my_reservations.html', {
        'made_reservations': made_reservations,
        'received_reservations': received_reservations,
        'is_abonned': is_abonned,
    })
