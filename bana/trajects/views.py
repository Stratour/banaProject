import re
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions, get_place_details
from django.conf import settings
from django.contrib import messages
from accounts.models import Child
from stripe_sub.models import Subscription
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm, SimpleProposedTrajectForm, ResearchedTrajectForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import datetime, timedelta, date
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance


def find_matching_trajects(obj, default_radius_km=5, time_tolerance_minutes=45):
    """
    Matching 100% ORM/SQL (PostGIS). Retourne une liste d'objets (ProposedTraject ou ResearchedTraject).
    - Symétrique : Parent recherche ↔ Propositions ; Proposition ↔ Recherches
    - Trajet simple Yaya : rayon = search_radius_km
    - Trajet normal : rayon = default_radius_km (5)
    - Vérifie transport, date, horaires (±time_tolerance), places/enfants.
    """
    time_tolerance = timedelta(minutes=time_tolerance_minutes)

    def time_ok(t1, t2):
        if not t1 or not t2:
            return True
        dt1 = datetime.combine(date.today(), t1)
        dt2 = datetime.combine(date.today(), t2)
        return (dt1 - time_tolerance) <= dt2 <= (dt1 + time_tolerance)

    # ---------------- Parent recherche -> match avec Propositions ----------------
    if isinstance(obj, ResearchedTraject):
        if not obj.traject or not obj.traject.start_point:
            return []

        base_qs = ProposedTraject.objects.filter(date=obj.date, is_active=True).exclude(user=obj.user)

        # Large pré-filtre de départ en DB (évite de ramener tout le monde)
        # Utilise une marge (par ex  max(default*5, 50km)) pour inclure trajets simples larges
        prefilter_radius = max(default_radius_km * 5, 50)
        base_qs = base_qs.annotate(
            distance_start=Distance('traject__start_point', obj.traject.start_point)
        ).filter(distance_start__lte=D(km=prefilter_radius))

        # On va construire un Q final correspondant aux PKs valides
        valid_pks = []

        for p in base_qs:
            # 1) rayon effectif (si simple on respecte le search_radius_km)
            rayon = (getattr(p, 'search_radius_km', None) or default_radius_km) if getattr(p, 'is_simple', False) else default_radius_km

            # 2) vérifier start_point exists
            if not p.traject.start_point:
                continue

            # 3) distance départ (utilise distance_start annoté pour perf)
            if p.distance_start is None:
                # fallback compute
                dist = p.traject.start_point.distance(obj.traject.start_point)
            else:
                dist = p.distance_start.m  # meters

            if dist > D(km=rayon).m:
                continue

            # 4) transport
            if not set(obj.transport_modes.all()).intersection(p.transport_modes.all()):
                continue

            # 5) if p normal -> check arrival and times
            if not getattr(p, 'is_simple', False):
                if not (obj.traject.end_point and p.traject.end_point):
                    continue
                # compute end distance (meters)
                d_end = p.traject.end_point.distance(obj.traject.end_point)
                if d_end > D(km=rayon).m:
                    continue
                if not (time_ok(obj.departure_time, p.departure_time) and time_ok(obj.arrival_time, p.arrival_time)):
                    continue

            # 6) places
            #if getattr(p, 'number_of_places', 9999) < getattr(obj, 'number_of_children', 1):
            #    continue

            valid_pks.append(p.pk)

        if not valid_pks:
            return []

        # final queryset ordered by real distance
        qs = ProposedTraject.objects.filter(pk__in=valid_pks).annotate(
            distance_start=Distance('traject__start_point', obj.traject.start_point)
        ).order_by('distance_start')

        return list(qs)

    # ---------------- Proposition (Yaya ou Parent) -> match avec Recherches ----------------
    if isinstance(obj, ProposedTraject):
        if not obj.traject or not obj.traject.start_point:
            return []

        # rayon effectif pour CE proposed
        rayon = (getattr(obj, 'search_radius_km', None) or default_radius_km) if getattr(obj, 'is_simple', False) else default_radius_km

        base_qs = ResearchedTraject.objects.filter(date=obj.date, is_active=True).exclude(user=obj.user)
        base_qs = base_qs.annotate(distance_start=Distance('traject__start_point', obj.traject.start_point)).filter(distance_start__lte=D(km=max(rayon, 50)))

        valid_pks = []
        for r in base_qs:
            if not r.traject.start_point:
                continue

            dist = r.distance_start.m if r.distance_start is not None else r.traject.start_point.distance(obj.traject.start_point)
            if dist > D(km=rayon).m:
                continue

            # transport
            if not set(obj.transport_modes.all()).intersection(r.transport_modes.all()):
                continue

            # if obj simple -> only departure matters (and date/transport)
            if getattr(obj, 'is_simple', False):
                valid_pks.append(r.pk)
                continue

            # else check arrival and times
            if not (obj.traject.end_point and r.traject.end_point):
                continue
            d_end = obj.traject.end_point.distance(r.traject.end_point)
            if d_end > D(km=rayon).m:
                continue
            if not (time_ok(obj.departure_time, r.departure_time) and time_ok(obj.arrival_time, r.arrival_time)):
                continue

            # places
            #if getattr(obj, 'number_of_places', 0) < getattr(r, 'number_of_children', 1):
            #    continue

            valid_pks.append(r.pk)

        if not valid_pks:
            return []

        qs = ResearchedTraject.objects.filter(pk__in=valid_pks).annotate(
            distance_start=Distance('traject__start_point', obj.traject.start_point)
        ).order_by('distance_start')

        return list(qs)

    return []


@login_required
def my_matchings_researched(request):
    """
    Parent (user) recherche → affiche les propositions correspondantes
    avec matching strict basé sur la géolocalisation.
    """
    user = request.user
    matches = []

    researched_matches = ResearchedTraject.objects.filter(
        user=user, is_active=True, date__gte=date.today()
    )
    is_abonned = Subscription.is_user_abonned(user)

    for research in researched_matches:
        matched_proposals = find_matching_trajects(research,default_radius_km=50)
        if matched_proposals:
            matches.append({'research': research, 'proposals': matched_proposals})

    return render(request, 'trajects/my_matchings_researched.html', {
        'matches': matches,
        'is_abonned': is_abonned
    })

@login_required
def my_matchings_proposed(request):
    """
    Parent/Yaya propose un trajet → affiche les recherches correspondantes
    avec matching strict basé sur la géolocalisation.
    """
    user = request.user
    matches = []

    proposed_matches = ProposedTraject.objects.filter(
        user=user, is_active=True, date__gte=date.today()
    )
    is_abonned = Subscription.is_user_abonned(user)

    for proposed in proposed_matches:
        # Rayon effectif : trajet simplifié Yaya ou normal
        rayon = proposed.search_radius_km if getattr(proposed, "is_simple", False) else 5
        matched_requests = find_matching_trajects(proposed, default_radius_km=rayon)
        if matched_requests:
            matches.append({'proposal': proposed, 'requests': matched_requests})

    return render(request, 'trajects/my_matchings_proposed.html', {
        'matches': matches,
        'is_abonned': is_abonned
    })
    
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


# ============================
#  Vues création de trajets
# ============================

@login_required
def proposed_traject(request, researchesTraject_id=None):
    """
    Vue pour qu’un parent propose un trajet (yaya).
    - Si POST : enregistre le trajet proposé.
    - Sinon : affiche un formulaire vide.
    """
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
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        traject_form = TrajectForm()
        proposed_form = ProposedTrajectForm()

    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form,
        'researched_traject': researchesTraject_id,
        'days_of_week': [
            ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'),
            ('4', 'Jeudi'), ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche'),
        ],
    }
    return render(request, 'trajects/proposed_traject.html', context)


def save_proposed_traject(request, traject_form, proposed_form):
    """
    Save proposed traject(s) robustly: ensure points have SRID, pass down search_radius etc.
    """
    if traject_form.is_valid() and proposed_form.is_valid():
        traject = traject_form.save(commit=False)

        # --- Récupération coordonnées via Google ---
        start_place_id = traject_form.cleaned_data.get('start_place_id')
        end_place_id = traject_form.cleaned_data.get('end_place_id')

        if start_place_id:
            start_details = get_place_details(start_place_id)
            if "lat" in start_details and "lng" in start_details:
                traject.start_point = Point(start_details["lng"], start_details["lat"], srid=4326)

        if end_place_id:
            end_details = get_place_details(end_place_id)
            if "lat" in end_details and "lng" in end_details:
                traject.end_point = Point(end_details["lng"], end_details["lat"], srid=4326)

        traject.save()

        cleaned_data = proposed_form.cleaned_data
        # recurrence...
        recurrence_type = cleaned_data.get('recurrence_type')
        recurrence_interval = cleaned_data.get('recurrence_interval')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin') or date_debut
        selected_days = request.POST.getlist('tr_weekdays')
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        number_of_places = cleaned_data.get('number_of_places') or 1
        details = cleaned_data.get('details')
        is_simple = cleaned_data.get('is_simple', False)
        search_radius_km = cleaned_data.get('search_radius_km') if is_simple else None

        # validations
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

        # create proposals, ensure every ProposedTraject stores search_radius_km if simple
        proposed_trajects = []
        for date_obj in recurrent_dates:
            proposed = ProposedTraject(
                user=request.user,
                traject=traject,
                date=date_obj,
                departure_time=departure_time,
                arrival_time=arrival_time,
                is_simple=is_simple,
                number_of_places=number_of_places,
                details=details,
                recurrence_type=recurrence_type,
                recurrence_interval=recurrence_interval if recurrence_type != 'none' else None,
                recurrence_days=recurrence_days,
                date_debut=date_debut if recurrence_type != 'none' else None,
                date_fin=date_fin if recurrence_type != 'none' else None,
                search_radius_km=search_radius_km if is_simple else None,
            )
            proposed.save()
            proposed.transport_modes.set(cleaned_data.get('transport_modes'))
            if cleaned_data.get('languages'):
                proposed.languages.set(cleaned_data.get('languages'))
            proposed_trajects.append(proposed)

        return proposed_trajects, True

    return None, False


def generate_recurrent_proposals(request, recurrent_dates, traject,
                                 departure_time, arrival_time, number_of_places,
                                 details, recurrence_type, recurrence_interval,
                                 recurrence_days, date_debut, date_fin, cleaned_data):
    """
    Crée les objets ProposedTraject pour chaque date récurrente.
    """
    proposals = []
    for date_obj in recurrent_dates:
        proposed = ProposedTraject(
            user=request.user,
            traject=traject,
            date=date_obj,
            departure_time=departure_time,
            arrival_time=arrival_time,
            number_of_places=number_of_places,
            details=details,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval if recurrence_type != 'none' else None,
            recurrence_days=recurrence_days,
            date_debut=date_debut if recurrence_type != 'none' else None,
            date_fin=date_fin if recurrence_type != 'none' else None,
        )
        proposed.save()
        proposed.transport_modes.set(cleaned_data.get('transport_modes'))
        proposed.languages.set(cleaned_data.get('languages'))

        proposals.append(proposed)
    return proposals


@login_required
def my_proposed_trajects(request):
    """Affiche tous les trajets proposés par l'utilisateur"""
    user_trajects = ProposedTraject.objects.filter(user=request.user, is_active=True, date__gte=date.today()).order_by('date', 'departure_time')
    return render(request, 'trajects/my_proposed_trajects.html', {
        'proposed_trajects': user_trajects
    })


@login_required
def simple_proposed_traject(request):
    """ Proposition rapide d'un trajet (simplifiée pour les yayas). """
    if request.method == 'POST':
        form = SimpleProposedTrajectForm(request.POST)

        if form.is_valid():
            user = request.user
            start_adress = form.cleaned_data['start_adress']
            transport_modes = form.cleaned_data['transport_modes']
            date_debut = form.cleaned_data['date_debut']
            number_of_places = form.cleaned_data['number_of_places']
            search_radius_km = form.cleaned_data['search_radius_km']
            
            # Récupérer start_place_id pour la géolocalisation
            start_place_id = request.POST.get('start_place_id')

            traject = Traject.objects.create(
                start_adress=start_adress,
                end_adress="",  # Pas d'arrivée définie ici
            )
            
            if start_place_id:
                start_details = get_place_details(start_place_id)
                if "lat" in start_details and "lng" in start_details:
                    traject.start_point = Point(start_details["lng"], start_details["lat"], srid=4326)
                    traject.save()

            matched_any = False
            created_count = 0
            total_matches = 0

            proposed = ProposedTraject.objects.create(
                user=user,
                traject=traject,
                date=date_debut,  # CORRECTION : utiliser date_debut au lieu de date_obj
                is_simple=True,
                number_of_places=number_of_places,
                search_radius_km=search_radius_km
            )
            proposed.transport_modes.set(transport_modes)
            
            matches = find_matching_trajects(proposed)
            if matches:
                matched_any = True
                total_matches += len(matches)
            created_count += 1

            if matched_any:
                messages.success(request,
                                 f"{created_count} proposition(s) enregistrée(s) avec {total_matches} matching(s) trouvés dans un rayon de {search_radius_km} km.")                                              
                return redirect('my_matchings_proposed')
            else:
                messages.warning(request,
                                 f"{created_count} proposition(s) enregistrée(s), mais aucun matching trouvé dans un rayon de {search_radius_km} km.")
                return redirect('my_proposed_trajects')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = SimpleProposedTrajectForm()

    return render(request, 'trajects/simple_proposed_traject.html', {'form': form})
    
    
@login_required
def researched_traject(request):
    """
    Vue pour qu’un parent enregistre une recherche de trajet.
    - Si POST : enregistre le trajet recherché avec coordonnées.
    - Sinon : affiche le formulaire vide.
    """
    transport_modes = TransportMode.objects.all()
    service = getattr(request.user.profile, 'service', None)

    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)

        researched_trajects, success = save_researched_traject(request, traject_form, researched_form)

        if not traject_form.is_valid():
            print("Erreurs TrajectForm:", traject_form.errors)

        if not researched_form.is_valid():
            print("Erreurs ResearchedTrajectForm:", researched_form.errors)
            
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
                    ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'), ('4', 'Jeudi'),
                    ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche')
                ],
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
        researched_form = ResearchedTrajectForm(user=request.user)

        context = {
            'traject_form': traject_form,
            'researched_form': researched_form,
            'transport_modes': transport_modes,
            'days_of_week': [
                ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'), ('4', 'Jeudi'),
                ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche')
            ],
            'service': service,
        }

    return render(request, 'trajects/searched_traject.html', context)


def save_researched_traject(request, traject_form, researched_form):
    if traject_form.is_valid() and researched_form.is_valid():
        traject = traject_form.save(commit=False)

        start_place_id = traject_form.cleaned_data.get('start_place_id')
        end_place_id = traject_form.cleaned_data.get('end_place_id')

        if start_place_id:
            start_details = get_place_details(start_place_id)
            if "lat" in start_details and "lng" in start_details:
                traject.start_point = Point(start_details["lng"], start_details["lat"], srid=4326)

        if end_place_id:
            end_details = get_place_details(end_place_id)
            if "lat" in end_details and "lng" in end_details:
                traject.end_point = Point(end_details["lng"], end_details["lat"], srid=4326)

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

        researched_trajects = []
        for date_instance in recurrent_dates:
            researched = ResearchedTraject(
                user=request.user,
                traject=traject,
                date=date_instance,
                departure_time=departure_time,
                arrival_time=arrival_time,
                recurrence_type=recurrence_type,
                recurrence_interval=recurrence_interval if recurrence_type != 'one_week' else None,
                recurrence_days=recurrence_days,
                date_debut=date_debut if recurrence_type != 'one_week' else None,
                date_fin=date_fin if recurrence_type != 'one_week' else None
            )
            researched.save()
            researched.transport_modes.set(cleaned_data.get('transport_modes'))
            if cleaned_data.get('children'):
                researched.children.set(cleaned_data.get('children'))
            researched_trajects.append(researched)

        return researched_trajects, True

    return None, False


def generate_recurrent_researches(request, recurrent_dates, traject,
                                  departure_time, arrival_time,
                                  recurrence_type, recurrence_interval,
                                  recurrence_days, date_debut, date_fin,
                                  cleaned_data):
    recurrent_researches = []
    for date_instance in recurrent_dates:
        researched = ResearchedTraject(
            user=request.user,
            traject=traject,
            date=date_instance,
            departure_time=departure_time,
            arrival_time=arrival_time,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval if recurrence_type != 'one_week' else None,
            recurrence_days=recurrence_days,
            date_debut=date_debut if recurrence_type != 'one_week' else None,
            date_fin=date_fin if recurrence_type != 'one_week' else None
        )
        researched.save()
        researched.transport_modes.set(cleaned_data.get('transport_modes'))
        researched.children.set(cleaned_data.get('children'))

        recurrent_researches.append(researched)

    return recurrent_researches


@login_required
def my_researched_trajects(request):
    """
    Affiche toutes les recherches de trajet actives de l’utilisateur
    """
    user_trajects = ResearchedTraject.objects.filter(
        user=request.user,
        is_active=True,
        date__gte=date.today()
    ).order_by('date', 'departure_time')

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
    if isinstance(suggestions, str):  # Si c'est une erreur
        return JsonResponse({"error": suggestions}, status=500)

    return JsonResponse({"suggestions": suggestions}, status=200)

def place_details_view(request):
    place_id = request.GET.get("place_id")
    if not place_id:
        return JsonResponse({"error": "Le paramètre 'place_id' est requis."}, status=400)

    details = get_place_details(place_id)

    if "error" in details:
        return JsonResponse(details, status=500)

    return JsonResponse(details, status=200)

# ====================')= reservation page ====================')==== #

@login_required
def manage_reservation(request, reservation_id, action):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Vérifier que l'utilisateur est bien le yaya (propriétaire du trajet proposé)
    if reservation.proposed_traject.user != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette réservation.")
        return redirect('my_reservations')

    # Vérifier si déjà traitée
    if reservation.status != 'pending':
        messages.warning(request, "Cette réservation a déjà été traitée.")
        return redirect('my_reservations')

    if action == 'accept':
        requested_places = reservation.number_of_places
        available_places = reservation.proposed_traject.number_of_places

        if requested_places > available_places:
            messages.error(request, "Il n'y a plus assez de places disponibles.")
            return redirect('my_reservations')

        reservation.status = 'confirmed'
        reservation.save()

        # Envoi d'un email de confirmation au parent
        parent_email = reservation.user.email
        yaya_name = request.user.profile.verified_first_name
        trajet_info = f"{reservation.proposed_traject.traject.start_adress} → {reservation.proposed_traject.traject.end_adress}"

        send_mail(
            subject="Réservation confirmée sur Bana",
            message=(
                f"Bonjour,\n\n"
                f"Votre demande de réservation pour le trajet {trajet_info} "
                f"({requested_places} enfant(s)) a été confirmée.\n\n"
                "Connectez-vous à Bana pour plus d'informations et prendre contact avec le Yaya. http://www.bana.mobi/trajects/my_reserve/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False,
        )

        # Mettre à jour les places
        reservation.proposed_traject.number_of_places -= requested_places
        reservation.proposed_traject.save()

        if reservation.proposed_traject.number_of_places <= 0:
            reservation.proposed_traject.is_active = False
            reservation.proposed_traject.save()

        messages.success(request, "Réservation confirmée.")

    elif action == 'reject':
        reservation.status = 'canceled'
        reservation.save()

        parent_email = reservation.user.email
        yaya_name = request.user.profile.verified_first_name
        trajet_info = f"{reservation.proposed_traject.traject.start_adress} → {reservation.proposed_traject.traject.end_adress}"

        send_mail(
            subject="Réservation refusée ou annulée",
            message=(
                f"Bonjour,\n\n"
                f"Votre demande de réservation pour le trajet {trajet_info} "
                f"({requested_places} enfant(s)) a été déclinée ou le trajet n'est plus disponible.\n\n"
                "N'hésitez pas à rechercher un autre accompagnateur. http://www.bana.mobi/trajects/researched_traject/"
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
    proposed_traject = get_object_or_404(ProposedTraject, id=proposed_id)

    if proposed_traject.user == request.user:
        messages.error(request, "Vous ne pouvez pas réserver votre propre trajet.")
        return redirect('my_matchings_researched')

    # Vérifier si réservation déjà existante
    existing = Reservation.objects.filter(
        user=request.user,
        proposed_traject=proposed_traject,
        researched_traject_id=researched_id
    ).exclude(status="canceled").exists()

    if existing:
        messages.warning(request, "Vous avez déjà une réservation en cours pour ce trajet.")
        return redirect('my_reservations')
    
    researched_traject = get_object_or_404(ResearchedTraject, id=researched_id, user=request.user)
    requested_places = researched_traject.children.count()

    reservation = Reservation.objects.create(
        user=request.user,
        proposed_traject=proposed_traject,
        researched_traject=researched_traject,
        number_of_places=requested_places,
        status='pending'
    )
    reservation.transport_modes.set(researched_traject.transport_modes.all())

    proposer_email = proposed_traject.user.email
    parent_name = request.user.profile.verified_first_name
    trajet_info = f"{proposed_traject.traject.start_adress} → {proposed_traject.traject.end_adress}"

    send_mail(
        subject="Nouvelle demande de réservation reçue",
        message=(
            f"Bonjour,\n\n"
            f"Vous avez reçu une nouvelle demande de réservation.\n\n"
            f"Détails du trajet : {trajet_info}\n"
            f"Nombre d'enfant(s) demandé(s) : {requested_places}\n\n"
            "Connectez-vous à Bana pour accepter ou refuser la demande. http://www.bana.mobi/trajects/my_reserve/"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[proposer_email],
        fail_silently=False,
    )

    messages.success(request, "Votre demande de réservation a été envoyée.")
    return redirect('my_reservations')


@login_required
def my_reservations(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    # Réservations faites par le parent
    made_reservations = Reservation.objects.filter(user=user).select_related(
        'proposed_traject', 'researched_traject', 'proposed_traject__traject', 'researched_traject__traject'
    )

    # Réservations reçues par le yaya
    received_reservations = Reservation.objects.filter(proposed_traject__user=user).select_related(
        'user', 'proposed_traject', 'researched_traject', 'proposed_traject__traject', 'researched_traject__traject'
    )

    return render(request, 'trajects/my_reservations.html', {
        'made_reservations': made_reservations,
        'received_reservations': received_reservations,
        'is_abonned': is_abonned,
    })


@login_required
def propose_help(request, researched_id):
    research = get_object_or_404(ResearchedTraject, id=researched_id)

    session_key = f"help_notified_{request.user.id}_{researched_id}"
    if request.session.get(session_key, False):
        messages.info(request, "Vous avez déjà signalé votre disponibilité pour ce trajet.")
        return redirect('my_matchings_proposed')
    request.session[session_key] = True

    parent_email = research.user.email
    trajet_info = f"{research.traject.start_adress} → {research.traject.end_adress}"
    date_str = research.date.strftime("%d/%m/%Y") if research.date else ""
    heure_depart = research.departure_time.strftime("%H:%M") if research.departure_time else "—"

    send_mail(
        subject="Recherche de trajet disponible",
        message=(
            f"Bonjour,\n\n"
            f"Bonne nouvelle ! Un accompagnateur est disponible pour votre recherche de trajet :\n\n"
            f"{trajet_info} le {date_str} (départ à {heure_depart}).\n\n"
            "Connectez-vous à Bana pour consulter les trajets disponible et effectuer une réservation. http://www.bana.mobi/trajects/matchings/parent/"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[parent_email],
        fail_silently=False,
    )

    messages.success(request, "Votre aide a été proposée et le parent a été informé par email.")
    return redirect('my_matchings_proposed')
