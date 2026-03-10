import re
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils.geocoding import get_autocomplete_suggestions, get_place_details
from django.conf import settings
from django.contrib import messages
from accounts.models import Child, FavoriteAddress
from stripe_sub.models import Subscription
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm, SimpleProposedTrajectForm, ResearchedTrajectForm
from django.db.models import Q, Min, Max, Count
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import datetime, timedelta, date
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Sum, Max
import uuid
from django.utils import timezone
from django.db import transaction

from django.contrib.auth import get_user_model

User = get_user_model()

def _available_places(proposal):
    """Places restantes = number_of_places (déjà décrémenté lors des confirmations)."""
    try:
        return max(0, int(proposal.number_of_places or 0))
    except (TypeError, ValueError):
        return 0

def _confirmed_reserved_places_for_proposal(proposal):
    """
    OPTIONNEL: total de places confirmées.
    ⚠️ NE PAS utiliser ce total pour retrancher à number_of_places
    si number_of_places est déjà un 'reste'.
    """
    return Reservation.objects.filter(
        proposed_traject=proposal,
        status='confirmed'
    ).aggregate(s=Sum('number_of_places'))['s'] or 0


def find_matching_trajects(obj, default_radius_km=5, time_tolerance_minutes=45):
    """
    Matching géographique et logique entre ResearchedTraject et ProposedTraject.
    - Ne masque plus les trajets confirmés : tout reste visible.
    - Vérifie uniquement distance, horaires, transports et places.
    """
    time_tolerance = timedelta(minutes=time_tolerance_minutes)

    def time_ok(t1, t2):
        """Compare deux heures avec une tolérance donnée."""
        if not t1 or not t2:
            return True
        dt1 = datetime.combine(date.today(), t1)
        dt2 = datetime.combine(date.today(), t2)
        return (dt1 - time_tolerance) <= dt2 <= (dt1 + time_tolerance)

    # ======================================================
    # 🧭 CAS 1 : Parent → match avec les propositions
    # ======================================================
    if isinstance(obj, ResearchedTraject):
        if not obj.traject or not obj.traject.start_point:
            return []

        # Propositions visibles tant qu'il reste des places et date égale
        base_qs = (
            ProposedTraject.objects
            .filter(date=obj.date, is_active=True)
            .exclude(user=obj.user)
            .annotate(distance_start=Distance('traject__start_point', obj.traject.start_point))
            .filter(distance_start__lte=D(km=max(default_radius_km * 5, 50)))  # pré-filtre large
        )

        valid_pks = []

        for p in base_qs:
            rayon = p.search_radius_km if getattr(p, 'is_simple', False) else default_radius_km

            # Distance départ
            if not p.traject.start_point:
                continue
            dist = p.distance_start.m if p.distance_start is not None else p.traject.start_point.distance(obj.traject.start_point)
            if dist > D(km=rayon).m:
                continue

            # Modes de transport
            if not set(obj.transport_modes.all()).intersection(p.transport_modes.all()):
                continue

            # Trajet simple
            if getattr(p, 'is_simple', False):
                valid_pks.append(p.pk)
                continue

            # Arrivée et horaires
            if not (obj.traject.end_point and p.traject.end_point):
                continue
            d_end = p.traject.end_point.distance(obj.traject.end_point)
            if d_end > D(km=rayon).m:
                continue
            if not (time_ok(obj.departure_time, p.departure_time) and time_ok(obj.arrival_time, p.arrival_time)):
                continue

            valid_pks.append(p.pk)

        return list(ProposedTraject.objects.filter(pk__in=valid_pks).order_by('date'))

    # ======================================================
    # 🚗 CAS 2 : Yaya → match avec les recherches
    # ======================================================
    if isinstance(obj, ProposedTraject):
        if not obj.traject or not obj.traject.start_point:
            return []

        rayon = obj.search_radius_km if getattr(obj, 'is_simple', False) else default_radius_km

        base_qs = (
            ResearchedTraject.objects
            .filter(date=obj.date, is_active=True)
            .exclude(user=obj.user)
            .annotate(distance_start=Distance('traject__start_point', obj.traject.start_point))
            .filter(distance_start__lte=D(km=max(rayon, 50)))
        )

        valid_pks = []

        for r in base_qs:
            if not r.traject.start_point:
                continue
            dist = r.distance_start.m if r.distance_start is not None else r.traject.start_point.distance(obj.traject.start_point)
            if dist > D(km=rayon).m:
                continue

            if not set(obj.transport_modes.all()).intersection(r.transport_modes.all()):
                continue

            #required_children = r.children.count() if hasattr(r, 'children') and r.children.exists() else 1
            #if _available_places(obj) < required_children:
            #    continue

            if getattr(obj, 'is_simple', False):
                valid_pks.append(r.pk)
                continue

            if not (obj.traject.end_point and r.traject.end_point):
                continue
            d_end = obj.traject.end_point.distance(r.traject.end_point)
            if d_end > D(km=rayon).m:
                continue
            if not (time_ok(obj.departure_time, r.departure_time) and time_ok(obj.arrival_time, r.arrival_time)):
                continue

            valid_pks.append(r.pk)

        return list(ResearchedTraject.objects.filter(pk__in=valid_pks).order_by('date'))

    return []


# ============================================================
# 💾 Enregistrement des trajets proposés et recherchés
# ============================================================

def save_proposed_traject(request, traject_form, proposed_form, groupe_name=None, groupe_uid=None):
    """Sauvegarde d’un trajet proposé (avec récurrence et géolocalisation)."""
    if traject_form.is_valid() and proposed_form.is_valid():
        traject = traject_form.save(commit=False)

        # Récupération des coordonnées via Google API
        for field in ["start_place_id", "end_place_id"]:
            place_id = traject_form.cleaned_data.get(field)
            if place_id:
                details = get_place_details(place_id)
                if "lat" in details and "lng" in details:
                    point = Point(details["lng"], details["lat"])
                    if "start" in field:
                        traject.start_point = point
                    else:
                        traject.end_point = point

        traject.save()
    
        cleaned = proposed_form.cleaned_data
        recurrence_type = cleaned.get('recurrence_type')
        recurrence_interval = cleaned.get('recurrence_interval')
        date_debut = cleaned.get('date_debut')
        date_fin = cleaned.get('date_fin') or date_debut
        selected_days = request.POST.getlist('tr_weekdays')
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        groupe_name = (groupe_name or "").strip() or "Mon trajet"
        groupe_uid = groupe_uid or uuid.uuid4()
        
        recurrent_dates = generate_recurrent_dates(
            date_debut=date_debut,
            date_fin=date_fin,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            specific_days=selected_days
        )

        proposed_trajects = generate_recurrent_proposals(
            request=request,
            recurrent_dates=recurrent_dates,
            traject=traject,
            departure_time=cleaned.get('departure_time'),
            arrival_time=cleaned.get('arrival_time'),
            number_of_places=cleaned.get('number_of_places', 1),
            details=cleaned.get('details'),
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            cleaned_data=cleaned,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        return proposed_trajects, True
    return None, False


def save_researched_traject(request, traject_form, researched_form, groupe_name=None, groupe_uid=None):
    """Sauvegarde d’un trajet recherché (Parent)."""
    if traject_form.is_valid() and researched_form.is_valid():
        traject = traject_form.save(commit=False)

        for field in ["start_place_id", "end_place_id"]:
            place_id = traject_form.cleaned_data.get(field)
            if place_id:
                details = get_place_details(place_id)
                if "lat" in details and "lng" in details:
                    point = Point(details["lng"], details["lat"])
                    if "start" in field:
                        traject.start_point = point
                    else:
                        traject.end_point = point

        traject.save()

        cleaned = researched_form.cleaned_data
        recurrence_type = cleaned.get('recurrence_type')
        recurrence_interval = cleaned.get('recurrence_interval')
        date_debut = cleaned.get('date_debut')
        date_fin = cleaned.get('date_fin') or date_debut
        selected_days = request.POST.getlist('tr_weekdays')
        recurrence_days = "|" + "|".join(selected_days) + "|" if selected_days else None

        groupe_name = (groupe_name or "").strip() or "Ma recherche"
        groupe_uid = groupe_uid or uuid.uuid4()
        
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
            departure_time=cleaned.get('departure_time'),
            arrival_time=cleaned.get('arrival_time'),
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            cleaned_data=cleaned,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        return researched_trajects, True

    return None, False

def save_simple_proposed_traject(request, form, groupe_name=None, groupe_uid=None):
    """
    Sauvegarde d’un ou plusieurs trajets simplifiés.
    Gère la géolocalisation, la récurrence et la création des ProposedTraject.
    """
    if not form.is_valid():
        return None, False

    user = request.user
    groupe_name = (groupe_name or "").strip() or "Mon trajet"
    groupe_uid = groupe_uid or uuid.uuid4()
    start_adress = form.cleaned_data['start_adress']
    transport_modes = form.cleaned_data['transport_modes']

    # ✅ Conversion et valeur par défaut
    number_of_places = int(form.cleaned_data.get('number_of_places') or 1)
    search_radius_km = form.cleaned_data['search_radius_km']

    # 🔁 Gestion de la récurrence
    recurrence_type = form.cleaned_data.get('recurrence_type')
    recurrence_interval = form.cleaned_data.get('recurrence_interval')
    date_debut = form.cleaned_data.get('date_debut')
    date_fin = form.cleaned_data.get('date_fin') or date_debut
    tr_weekdays = form.cleaned_data.get('tr_weekdays')

    recurrent_dates = generate_recurrent_dates(
        date_debut=date_debut,
        date_fin=date_fin,
        recurrence_type=recurrence_type,
        recurrence_interval=recurrence_interval,
        specific_days=tr_weekdays,

    )

    # 🗺️ Création du Traject (point de départ uniquement)
    traject = Traject.objects.create(start_adress=start_adress, end_adress="")

    start_place_id = request.POST.get('start_place_id')
    if start_place_id:
        start_details = get_place_details(start_place_id)
        if "lat" in start_details and "lng" in start_details:
            traject.start_point = Point(start_details["lng"], start_details["lat"], srid=4326)
            traject.save()

    # 🚗 Création des trajets proposés récurrents
    proposed_trajects = []
    for date_obj in recurrent_dates:
        proposed = ProposedTraject.objects.create(
            user=user,
            traject=traject,
            date=date_obj,
            is_simple=True,
            number_of_places=number_of_places,  # ✅ Correction ici
            search_radius_km=search_radius_km,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )
        proposed.transport_modes.set(transport_modes)
        proposed_trajects.append(proposed)

    return proposed_trajects, True

# ============================================================
# 🧭 VUES UTILISATEURS
# ============================================================

@login_required
def my_proposed_trajects(request):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    # 1) On récupère les groupes (uid + stats)
    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=False)
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            count=Count('id')
        )
        .order_by('-last_date')
    )

    # 2) Pour chaque groupe, on prend 1 occurrence "header" (objet complet)
    proposed_headers = []
    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, groupe_uid=g['groupe_uid'], is_active=True)
            .order_by('date', 'departure_time')
            .first()
        )

        if not header:
            continue
        
        # ✅ On “colle” des infos de groupe sur l’objet pour le template
        header.groupe_count = g['count']
        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']

        proposed_headers.append(header)

    return render(request, 'trajects/my_proposed_trajects.html', {
        'proposed_trajects': proposed_headers,  
        'is_abonned': is_abonned,
    })



@login_required
def my_simple_trajects(request):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_simple=True, is_active=True)
        .values('groupe_uid')
        .annotate(first_date=Min('date'), last_date=Max('date'), count=Count('id'))
        .order_by('-last_date')
    )

    headers = []
    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, is_simple=True, is_active=True, groupe_uid=g['groupe_uid'])
            .order_by('date', 'departure_time')
            .first()
        )
        if not header:
            continue
        
        header.groupe_count = g['count']
        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        headers.append(header)

    return render(request, 'trajects/my_simple_trajects.html', {
        'simple_trajects': headers,
        'is_abonned': is_abonned,
    })
    


def my_researched_trajects(request):
    """
    Liste les recherches de trajets actives du parent.
    """
    """user_trajects = ResearchedTraject.objects.filter(
        user=request.user,
        is_active=True,
        date__gte=date.today()
    ).order_by('date', 'departure_time')
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)
    
    groupes = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True)
        .values('groupe_uid',)
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            count=Count('id')
        )
        .order_by('-last_date')
    )
    
    researched_headers = []
    for g in groupes:
        header = (
            ResearchedTraject.objects
            .filter(user=user, groupe_uid=g['groupe_uid'], is_active=True)
            .order_by('date', 'departure_time')
            .first()
        )
        if not header:
            continue
        
        # ✅ On “colle” des infos de groupe sur l’objet pour le template
        header.groupe_count = g['count']
        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']

        researched_headers.append(header)


    return render(request, 'trajects/my_researched_trajects.html', {
        'researched_trajects': researched_headers,
        'is_abonned': is_abonned,
    })

# ============================================================
# 🔵 Matching des trajets proposés classiques
# ============================================================

@login_required
def my_matchings_proposed(request):
    """
    Yaya → affiche ses groupes proposés (header complet)
    + liste des parents (objets User) qui matchent par groupe.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groups_out = []

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='pending')
        .values_list('researched_traject_id', flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='confirmed')
        .values_list('researched_traject_id', flat=True)
    )

    # ✅ Groupes de trajets proposés (Option A : période complète)
    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=False)
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            count=Count('id')
        )
        .order_by('-last_date')
    )

    for g in groupes:

        # Header complet
        header = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g['groupe_uid'])
            .select_related('traject')
            .prefetch_related('transport_modes', 'languages')
            .order_by('date', 'departure_time')
            .first()
        )
        if not header:
            continue

        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        header.groupe_count = g['count']

        occurrences = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g['groupe_uid'])
            .order_by('date', 'departure_time')
        )

        matched_researched_ids = set()

        # Accumuler toutes les recherches matchées
        for proposed in occurrences:
            rayon = proposed.search_radius_km or 5
            matched = find_matching_trajects(proposed, default_radius_km=rayon)

            if hasattr(matched, "values_list"):
                matched_researched_ids.update(matched.values_list('id', flat=True))
            else:
                matched_researched_ids.update([m.id for m in matched])

        if not matched_researched_ids:
            continue

        # 🔥 Agrégation par (parent_user_id, researched_groupe_uid)
        raw = (
            ResearchedTraject.objects
            .filter(id__in=matched_researched_ids, is_active=True)
            .values('user_id', 'groupe_uid')
            .annotate(
                first_date=Min('date'),
                last_date=Max('date'),
                count=Count('id')
            )
            .order_by('first_date')
        )

        parent_ids = [r['user_id'] for r in raw]
        parents_map = {
            u.id: u for u in User.objects.filter(id__in=parent_ids).select_related('profile')
        }

        matched_parents = []
        for r in raw:
            parent_obj = parents_map.get(r['user_id'])
            if not parent_obj:
                continue
            matched_parents.append({
                "user": parent_obj,
                "researched_groupe_uid": r['groupe_uid'],
                "first_date": r['first_date'],
                "last_date": r['last_date'],
                "count": r['count'],
            })

        groups_out.append({
            "header": header,
            "matched_users": matched_parents,
        })

    return render(request, 'trajects/my_matchings_proposed.html', {
        "groups": groups_out,
        "is_abonned": is_abonned,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })


# ============================================================
# 🟢 Matching des trajets simplifiés
# ============================================================

@login_required
def my_matchings_simple(request):
    """
    Yaya → correspondances des trajets simplifiés,
    groupées par groupe_uid côté ProposedTraject (is_simple=True),
    avec liste des parents matchés (objets User).
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groups_out = []

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='pending')
        .values_list('researched_traject_id', flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='confirmed')
        .values_list('researched_traject_id', flat=True)
    )

    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_simple=True, is_active=True)
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            count=Count('id')
        )
        .order_by('-last_date')
    )

    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, is_simple=True, is_active=True, groupe_uid=g['groupe_uid'])
            .select_related('traject')
            .prefetch_related('transport_modes')
            .order_by('date', 'departure_time')
            .first()
        )
        if not header:
            continue

        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        header.groupe_count = g['count']

        occurrences = (
            ProposedTraject.objects
            .filter(user=user, is_simple=True, is_active=True, groupe_uid=g['groupe_uid'])
            .order_by('date', 'departure_time')
        )

        matched_researched_ids = set()

        for proposed in occurrences:
            rayon = proposed.search_radius_km or 5
            matched = find_matching_trajects(proposed, default_radius_km=rayon)

            if hasattr(matched, "values_list"):
                matched_researched_ids.update(matched.values_list('id', flat=True))
            else:
                matched_researched_ids.update([m.id for m in matched])

        if not matched_researched_ids:
            continue

        # Regrouper par parent + groupe researched
        raw = (
            ResearchedTraject.objects
            .filter(id__in=matched_researched_ids, is_active=True)
            .values('user_id', 'groupe_uid')
            .annotate(
                first_date=Min('date'),
                last_date=Max('date'),
                count=Count('id')
            )
            .order_by('first_date')
        )

        parent_ids = [r['user_id'] for r in raw]
        parents_map = {
            u.id: u for u in User.objects.filter(id__in=parent_ids).select_related('profile')
        }

        matched_parents = []
        for r in raw:
            parent_obj = parents_map.get(r['user_id'])
            if not parent_obj:
                continue
            matched_parents.append({
                "user": parent_obj,
                "researched_groupe_uid": r['groupe_uid'],
                "first_date": r['first_date'],
                "last_date": r['last_date'],
                "count": r['count'],
            })

        groups_out.append({
            "header": header,
            "matched_users": matched_parents,
        })

    return render(request, "trajects/my_matchings_simple.html", {
        "groups": groups_out,
        "is_abonned": is_abonned,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })


# ============================================================
# 🟠 Matching des trajets recherchés (Parents)
# ============================================================

@login_required
def my_matchings_researched(request):
    """
    Parent → affiche ses groupes de recherches (header complet)
    + liste des yayas (objets User) qui matchent.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    matches_groupes = []

    groupes = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True)
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            count=Count('id')
        )
        .order_by('-last_date')
    )

    for g in groupes:
        header = (
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g['groupe_uid'])
            .select_related('traject')
            .prefetch_related('transport_modes', 'children')
            .order_by('date', 'departure_time')
            .first()
        )
        if not header:
            continue

        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        header.groupe_count = g['count']

        occurrences = (
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g['groupe_uid'])
            .order_by('date', 'departure_time')
        )

        matched_proposed_ids = set()
        for research in occurrences:
            matched = find_matching_trajects(research, default_radius_km=5)

            if hasattr(matched, "values_list"):
                matched_proposed_ids.update(matched.values_list('id', flat=True))
            else:
                matched_proposed_ids.update([m.id for m in matched])

        if not matched_proposed_ids:
            continue

        # Agrégation par (user_id, groupe_uid)
        raw = (
            ProposedTraject.objects
            .filter(id__in=matched_proposed_ids, is_active=True)
            .values('user_id', 'groupe_uid')
            .annotate(
                first_date=Min('date'),
                last_date=Max('date'),
                count=Count('id')
            )
            .order_by('first_date')
        )

        user_ids = [r['user_id'] for r in raw]
        users_map = {
            u.id: u for u in User.objects.filter(id__in=user_ids).select_related('profile')
        }

        matched_users = []
        for r in raw:
            u = users_map.get(r['user_id'])
            if not u:
                continue
            matched_users.append({
                "user": u,
                "proposed_groupe_uid": r['groupe_uid'],
                "first_date": r['first_date'],
                "last_date": r['last_date'],
                "count": r['count'],
            })

        matches_groupes.append({
            "header": header,
            "matched_users": matched_users,
        })

    return render(request, "trajects/my_matchings_researched.html", {
        "matches_groupes": matches_groupes,
        "is_abonned": is_abonned,
        "today": today,
    })


@login_required
def my_proposed_groupe_detail(request, groupe_uid):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = timezone.now().date()
    
    occurrences_all= (
        ProposedTraject.objects
        .filter(user=user, groupe_uid=groupe_uid, is_active=True, is_simple=False)
        .order_by('date', 'departure_time')
    )

    header = occurrences_all.first()

    # ✅ Stats réelles (toujours correctes)
    stats = occurrences_all.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )
    
    occurrences_upcoming = occurrences_all.filter(date__gte=today).order_by('date', 'departure_time')
    
    occurrences_past = occurrences_all.filter(date__lt=today).order_by('-date', '-departure_time')

    return render(request, 'trajects/my_proposed_groupe_detail.html', {
        'header': header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'is_abonned': is_abonned,
        'stats': stats,
        
    })
    
    
@login_required
def my_simple_groupe_detail(request, groupe_uid):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = timezone.now().date()
    
    occurrences_all = (
        ProposedTraject.objects
        .filter(user=user, is_simple=True, groupe_uid=groupe_uid, is_active=True)
        .order_by('date', 'departure_time')
    )
    header = occurrences_all.first()

    # ✅ Stats réelles (toujours correctes)
    stats = occurrences_all.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )
    
    occurrences_upcoming = occurrences_all.filter(date__gte=today).order_by('date', 'departure_time')
    
    occurrences_past = occurrences_all.filter(date__lt=today).order_by('-date', '-departure_time')

    
    return render(request, 'trajects/my_simple_groupe_detail.html', {
        'header': header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'stats': stats,
        'is_abonned': is_abonned,
    })
    
@login_required
def my_researched_groupe_detail(request, groupe_uid):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = timezone.now().date()
    
    occurrences_all = (
        ResearchedTraject.objects
        .filter(user=user, groupe_uid=groupe_uid, is_active=True)
        .order_by('date', 'departure_time')
    )

    researched_header = occurrences_all.first()

    # ✅ Stats réelles (toujours correctes)
    stats = occurrences_all.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    occurrences_upcoming = occurrences_all.filter(date__gte=today).order_by('date', 'departure_time')
    
    occurrences_past = occurrences_all.filter(date__lt=today).order_by('-date', '-departure_time')
    
    return render(request, 'trajects/my_researched_groupe_detail.html', {
        'header': researched_header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'is_abonned': is_abonned,
        'stats': stats,
    })
    
@login_required
def my_matchings_proposed_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    """
    Yaya → détail d'un matching entre :
    - ton groupe proposé : proposed_groupe_uid
    - le groupe recherché du parent : researched_groupe_uid
    - le parent : parent_user_id
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='pending')
        .values_list('researched_traject_id', flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='confirmed')
        .values_list('researched_traject_id', flat=True)
    )

    # ✅ Header = ton groupe proposé (sécurisé)
    proposed_qs = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=False, groupe_uid=proposed_groupe_uid)
        .select_related('traject')
        .prefetch_related('transport_modes', 'languages')
        .order_by('date', 'departure_time')
    )
    header = proposed_qs.first()
    if not header:
        return render(request, "trajects/my_matchings_proposed_detail.html", {
            "error": "Groupe proposé introuvable.",
            "is_abonned": is_abonned
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    # ✅ Groupe du parent correspondant
    researched_qs = (
        ResearchedTraject.objects
        .filter(
            user_id=parent_user_id,
            is_active=True,
            groupe_uid=researched_groupe_uid
        )
        .select_related('traject', 'user', 'user__profile')
        .prefetch_related('transport_modes', 'children')
        .order_by('date', 'departure_time')
    )
    parent_header = researched_qs.first()
    if not parent_header:
        return render(request, "trajects/my_matchings_proposed_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    # ✅ Construire les dates matchées = côté parent (ses dates) + actions
    matched_researched_ids = set()

    for proposed in proposed_qs:
        matched = find_matching_trajects(proposed, default_radius_km=5)
        if hasattr(matched, "values_list"):
            matched_researched_ids.update(matched.values_list('id', flat=True))
        else:
            matched_researched_ids.update([m.id for m in matched])

    # On ne garde que les recherches de CE parent + CE groupe
    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True
        )
        .select_related('traject', 'user', 'user__profile')
        .prefetch_related('transport_modes', 'children')
        .order_by('date', 'departure_time')
    )

    proposed_by_date = {p.date: p for p in proposed_qs}
    
    rows = []
    for r in matched_dates_qs:
        p = proposed_by_date.get(r.date)
        remaining = None
        
        if p and p.number_of_places is not None:
            remaining = max(0, p.number_of_places - p.confirmed_users.count())
        
        rows.append({
            "research": r,
            "is_past": bool(r.date and r.date < today),
            "children_count": r.children.count(),
            "remaining_places": remaining,
        })
       
    

    return render(request, 'trajects/my_matchings_proposed_detail.html', {
        "header": header,
        "proposed_stats": proposed_stats,

        "parent_header": parent_header,
        "parent_stats": parent_stats,

        "rows": rows,
        "is_abonned": is_abonned,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })
    
     
@login_required
def my_matchings_simple_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    """
    Yaya → détail matching Simple :
    - ton groupe simple (proposed_groupe_uid)
    - groupe recherché du parent (researched_groupe_uid)
    - parent identifié (parent_user_id)
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='pending')
        .values_list('researched_traject_id', flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status='confirmed')
        .values_list('researched_traject_id', flat=True)
    )

    # Header = ton groupe simple
    proposed_qs = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=True, groupe_uid=proposed_groupe_uid)
        .select_related('traject')
        .prefetch_related('transport_modes')
        .order_by('date', 'departure_time')
    )
    header = proposed_qs.first()
    if not header:
        return render(request, "trajects/my_matchings_simple_detail.html", {
            "error": "Groupe simple introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    # Header parent
    researched_qs = (
        ResearchedTraject.objects
        .filter(user_id=parent_user_id, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related('traject', 'user', 'user__profile')
        .prefetch_related('transport_modes', 'children')
        .order_by('date', 'departure_time')
    )
    parent_header = researched_qs.first()
    if not parent_header:
        return render(request, "trajects/my_matchings_simple_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned,
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    # Accumuler les researched matchés via toutes les occurrences simples
    matched_researched_ids = set()
    for proposed in proposed_qs:
        rayon = proposed.search_radius_km or 5
        matched = find_matching_trajects(proposed, default_radius_km=rayon)

        if hasattr(matched, "values_list"):
            matched_researched_ids.update(matched.values_list('id', flat=True))
        else:
            matched_researched_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True
        )
        .select_related('traject', 'user', 'user__profile')
        .prefetch_related('transport_modes', 'children')
        .order_by('date', 'departure_time')
    )

    # places restantes par date = occurrence simple du yaya ce jour-là
    proposed_by_date = {p.date: p for p in proposed_qs}

    rows = []
    for r in matched_dates_qs:
        p = proposed_by_date.get(r.date)
        remaining = None
        if p and p.number_of_places is not None:
            remaining = max(0, p.number_of_places - p.confirmed_users.count())

        rows.append({
            "research": r,
            "is_past": bool(r.date and r.date < today),
            "children_count": r.children.count(),
            "remaining_places": remaining,
            "radius_km": (p.search_radius_km if p else None),
            "transport_modes": (p.transport_modes.all() if p else []),
        })

    return render(request, "trajects/my_matchings_simple_detail.html", {
        "header": header,
        "proposed_stats": proposed_stats,

        "parent_header": parent_header,
        "parent_stats": parent_stats,

        "rows": rows,
        "is_abonned": is_abonned,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })
    
@login_required
def my_matchings_researched_detail(request, researched_groupe_uid, proposed_groupe_uid, yaya_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    researched_qs = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related('traject')
        .prefetch_related('transport_modes', 'children')
        .order_by('date', 'departure_time')
    )
    researched_header = researched_qs.first()
    if not researched_header:
        return render(request, "trajects/my_matchings_researched_detail.html", {
            "error": "Groupe de recherche introuvable.",
            "is_abonned": is_abonned,
        })

    matched_proposed_ids = set()
    for research in researched_qs:
        matched = find_matching_trajects(research, default_radius_km=5)
        if hasattr(matched, "values_list"):
            matched_proposed_ids.update(matched.values_list('id', flat=True))
        else:
            matched_proposed_ids.update([m.id for m in matched])

    if not matched_proposed_ids:
        return render(request, "trajects/my_matchings_researched_detail.html", {
            "researched_header": researched_header,
            "error": "Aucune correspondance trouvée pour ce groupe.",
            "is_abonned": is_abonned,
        })

    proposed_qs = (
        ProposedTraject.objects
        .filter(
            id__in=matched_proposed_ids,
            is_active=True,
            groupe_uid=proposed_groupe_uid,
            user_id=yaya_user_id,
        )
        .select_related('traject', 'user', 'user__profile')
        .prefetch_related('transport_modes', 'languages')
        .order_by('date', 'departure_time')
    )

    proposed_header = proposed_qs.first()
    if not proposed_header:
        return render(request, "trajects/my_matchings_researched_detail.html", {
            "researched_header": researched_header,
            "error": "Aucune date correspondante pour ce yaya et ce groupe.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min('date'),
        last_date=Max('date'),
        count=Count('id')
    )

    my_pending_proposal_ids = set(
        Reservation.objects.filter(user=user, status='pending')
        .values_list('proposed_traject_id', flat=True)
    )
    my_confirmed_proposal_ids = set(
        Reservation.objects.filter(user=user, status='confirmed')
        .values_list('proposed_traject_id', flat=True)
    )

    # ✅ Associer chaque proposal au research correspondant par date
    researched_by_date = {r.date: r for r in researched_qs}

    rows = []
    for p in proposed_qs:
        research = researched_by_date.get(p.date)
        if not research:
            continue

        rows.append({
            "proposal": p,
            "research": research,
            "is_past": bool(p.date and p.date < today),
        })

    return render(request, "trajects/my_matchings_researched_detail.html", {
        "researched_header": researched_header,
        "proposed_header": proposed_header,
        "proposed_stats": proposed_stats,
        "rows": rows,
        "is_abonned": is_abonned,
        "today": today,
        "my_pending_proposal_ids": my_pending_proposal_ids,
        "my_confirmed_proposal_ids": my_confirmed_proposal_ids,
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
        groupe_name = (request.POST.get('groupe_name') or '').strip() or "Mon trajet"
        groupe_uid = uuid.uuid4()
        
        proposed_trajects, success = save_proposed_traject(request, traject_form, proposed_form, groupe_name=groupe_name, groupe_uid=groupe_uid)

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

    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address")
    )
    
    context = {
        'traject_form': traject_form,
        'proposed_form': proposed_form,
        'researched_traject': researchesTraject_id,
        'fav_addresses': fav_addresses,
        'days_of_week': [
            ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'),
            ('4', 'Jeudi'), ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche'),
        ],
    }
    return render(request, 'trajects/proposed_traject.html', context)

def generate_recurrent_proposals(request, recurrent_dates, traject,
                                 departure_time, arrival_time, number_of_places,
                                 details, recurrence_type, recurrence_interval,
                                 recurrence_days, date_debut, date_fin, cleaned_data,
                                 groupe_name=None, groupe_uid=None):
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
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )
        proposed.save()
        proposed.transport_modes.set(cleaned_data.get('transport_modes'))
        proposed.languages.set(cleaned_data.get('languages'))

        proposals.append(proposed)
    return proposals


@login_required
def simple_proposed_traject(request):
    """Proposition d'un trajet simplifié (Yaya) avec récurrence et matching automatique."""
    
    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address")
    )
    
    if request.method == 'POST':
        form = SimpleProposedTrajectForm(request.POST)
        
        if form.is_valid():
            
            groupe_name = (request.POST.get('groupe_name') or '').strip() or "Mon trajet"
            groupe_uid = uuid.uuid4()
            proposed_trajects, success = save_simple_proposed_traject(request, form, groupe_name=groupe_name, groupe_uid=groupe_uid)

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
                        f"{created_count} trajet(s) simplifié(s) enregistré(s) avec {total_matches} matching(s) trouvés."
                    )
                    return redirect('my_matchings_simple')
                else:
                    messages.warning(
                        request,
                        f"{created_count} trajet(s) simplifié(s) enregistré(s), mais aucun matching trouvé."
                    )
                    return redirect('my_simple_trajects')
            else:
                messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = SimpleProposedTrajectForm()

    # ✅ Ajout des variables nécessaires pour l’affichage des jours
    days_of_week = [
        ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'),
        ('4', 'Jeudi'), ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche'),
    ]
    selected_days = request.POST.getlist('tr_weekdays') if request.method == 'POST' else []

    return render(request, 'trajects/simple_proposed_traject.html', {
        'form': form,
        'days_of_week': days_of_week,
        'tr_weekdays': selected_days,
        'fav_addresses': fav_addresses,
    })

    
@login_required
def researched_traject(request):
    """
    Vue pour qu’un parent enregistre une recherche de trajet.
    - Si POST : enregistre le trajet recherché avec coordonnées.
    - Sinon : affiche le formulaire vide.
    """
    transport_modes = TransportMode.objects.all()
    service = getattr(request.user.profile, 'service', None)

    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address")
    )
    
    if request.method == 'POST':
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)

        groupe_name = (request.POST.get('groupe_name') or '').strip() or "Ma recherche"
        groupe_uid = uuid.uuid4()
        
        researched_trajects, success = save_researched_traject(request, traject_form, researched_form, groupe_name=groupe_name, groupe_uid=groupe_uid)

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
                'fav_addresses': fav_addresses,
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
            'fav_addresses': fav_addresses,
            'days_of_week': [
                ('1', 'Lundi'), ('2', 'Mardi'), ('3', 'Mercredi'), ('4', 'Jeudi'),
                ('5', 'Vendredi'), ('6', 'Samedi'), ('7', 'Dimanche')
            ],
            'service': service,
        }

    return render(request, 'trajects/searched_traject.html', context)


def generate_recurrent_researches(request, recurrent_dates, traject,
                                  departure_time, arrival_time,
                                  recurrence_type, recurrence_interval,
                                  recurrence_days, date_debut, date_fin,
                                  cleaned_data, groupe_name=None, groupe_uid=None):
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
            date_fin=date_fin if recurrence_type != 'one_week' else None,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )
        researched.save()
        researched.transport_modes.set(cleaned_data.get('transport_modes'))
        researched.children.set(cleaned_data.get('children'))

        recurrent_researches.append(researched)

    return recurrent_researches

    
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
@transaction.atomic
def delete_proposed_groupe(request, groupe_uid):
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect('my_proposed_trajects', groupe_uid=groupe_uid)

    qs = ProposedTraject.objects.filter(
        user=request.user,
        groupe_uid=groupe_uid
    )

    if not qs.exists():
        messages.error(request, "Groupe introuvable.")
        return redirect('my_proposed_trajects')

    count = qs.count()
    qs.delete()

    messages.success(request, f"Groupe supprimé ({count} date(s)).")
    return redirect('my_proposed_trajects')

@login_required
def delete_proposed_traject(request, groupe_uid, pk):
    trajet = get_object_or_404(
        ProposedTraject,
        pk=pk,
        user=request.user,
        groupe_uid=groupe_uid
    )

    if request.method == "POST":
        trajet.delete()
        messages.success(request, "La date du trajet proposé a été supprimée.")
        return redirect('my_proposed_groupe_detail', groupe_uid=groupe_uid)

    messages.error(request, "Action non autorisée.")
    return redirect('my_proposed_groupe_detail', groupe_uid=groupe_uid)

@login_required
@transaction.atomic
def delete_simple_groupe(request, groupe_uid):
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect('my_simple_trajects', groupe_uid=groupe_uid)

    qs = ProposedTraject.objects.filter(
        user=request.user,
        groupe_uid=groupe_uid
    )

    if not qs.exists():
        messages.error(request, "Groupe introuvable.")
        return redirect('my_simple_trajects')

    count = qs.count()
    qs.delete()

    messages.success(request, f"Groupe supprimé ({count} date(s)).")
    return redirect('my_simple_trajects')

@login_required
def delete_simple_traject(request, groupe_uid, pk):
    trajet = get_object_or_404(
        ProposedTraject,
        pk=pk,
        user=request.user,
        groupe_uid=groupe_uid
    )

    if request.method == "POST":
        trajet.delete()
        messages.success(request, "La date du trajet recherché a été supprimée.")
        return redirect('my_simple_groupe_detail', groupe_uid=groupe_uid)

    messages.error(request, "Action non autorisée.")
    return redirect('my_simple_groupe_detail', groupe_uid=groupe_uid)
    
    
@login_required
def delete_researched_traject(request, groupe_uid, pk):
    trajet = get_object_or_404(
        ResearchedTraject,
        pk=pk,
        user=request.user,
        groupe_uid=groupe_uid
    )

    if request.method == "POST":
        trajet.delete()
        messages.success(request, "La date du trajet recherché a été supprimée.")
        return redirect('my_researched_groupe_detail', groupe_uid=groupe_uid)

    messages.error(request, "Action non autorisée.")
    return redirect('my_researched_groupe_detail', groupe_uid=groupe_uid)

@login_required
@transaction.atomic
def delete_researched_groupe(request, groupe_uid):
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect('my_researched_groupe_detail', groupe_uid=groupe_uid)

    qs = ResearchedTraject.objects.filter(
        user=request.user,
        groupe_uid=groupe_uid
    )

    if not qs.exists():
        messages.error(request, "Groupe introuvable.")
        return redirect('my_researched_trajects')

    count = qs.count()
    qs.delete()

    messages.success(request, f"Groupe supprimé ({count} date(s)).")
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

'''@login_required
def manage_reservation(request, reservation_id, action):
    """
    Accepter/Refuser une réservation.
    - 'accept' : status -> confirmed, décrémente number_of_places, NE TOUCHE PAS is_active.
    - 'reject' : status -> canceled, ne modifie pas les places.
    """
    reservation = get_object_or_404(
        Reservation.objects.select_related('proposed_traject', 'proposed_traject__traject', 'user'),
        id=reservation_id
    )
    proposed = reservation.proposed_traject

    if proposed.user != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette réservation.")
        return redirect('my_reservations')

    if reservation.status != 'pending':
        messages.warning(request, "Cette réservation a déjà été traitée.")
        return redirect('my_reservations')

    if action == 'accept':
        requested_places = int(reservation.number_of_places or 0)

        proposed.refresh_from_db()
        available_places = int(proposed.number_of_places or 0)

        if requested_places <= 0:
            messages.error(request, "Demande invalide : nombre de places demandé incorrect.")
            return redirect('my_reservations')

        if requested_places > available_places:
            messages.error(request, "Il n'y a plus assez de places disponibles.")
            return redirect('my_reservations')

        reservation.status = 'confirmed'
        reservation.save(update_fields=['status'])

        # Optionnel : trace M2M si tu l'utilises en affichage
        try:
            proposed.confirmed_users.add(reservation.user)
        except Exception:
            pass

        # Décrémenter uniquement le nombre de places restantes
        remaining = max(0, available_places - requested_places)
        proposed.number_of_places = remaining
        # ❌ ne pas toucher proposed.is_active ici
        proposed.save(update_fields=['number_of_places'])

        # Email info
        parent_email = reservation.user.email
        trajet_info = f"{proposed.traject.start_adress} → {proposed.traject.end_adress or '—'}"
        send_mail(
            subject="Réservation confirmée sur Bana",
            message=(
                f"Bonjour,\n\n"
                f"Votre demande de réservation pour le trajet {trajet_info} "
                f"({requested_places} enfant(s)) a été confirmée.\n\n"
                "Connectez-vous à Bana pour plus d'informations et prendre contact avec le Yaya. "
                "https://www.bana.mobi/trajets/mes-réservations/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False,
        )

        messages.success(request, "Réservation confirmée.")

    elif action == 'reject':
        reservation.status = 'canceled'
        reservation.save(update_fields=['status'])

        try:
            proposed.confirmed_users.remove(reservation.user)
        except Exception:
            pass

        parent_email = reservation.user.email
        trajet_info = f"{proposed.traject.start_adress} → {proposed.traject.end_adress or '—'}"
        send_mail(
            subject="Réservation refusée ou annulée",
            message=(
                f"Bonjour,\n\n"
                f"Votre demande de réservation pour le trajet {trajet_info} "
                f"a été déclinée ou le trajet n'est plus disponible.\n\n"
                "N'hésitez pas à rechercher un autre accompagnateur. "
                "https://www.bana.mobi/trajet/recherches/mes-recherches/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            fail_silently=False,
        )

        messages.success(request, "Réservation refusée.")
    else:
        messages.error(request, "Action invalide.")
        return redirect('my_reservations')

    return redirect('my_reservations')
'''

@login_required
def manage_reservation(request, reservation_id, action):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            'user', 'user__profile',
            'proposed_traject', 'proposed_traject__user',
            'researched_traject'
        ),
        id=reservation_id,
        proposed_traject__user=request.user
    )

    if action not in ['accept', 'reject']:
        messages.error(request, "Action invalide.")
        return redirect('my_reservations')

    if action == 'accept':
        if reservation.status == 'confirmed':
            messages.info(request, "Cette réservation est déjà confirmée.")
            return redirect('my_reservations')

        remaining_places = max(
            0,
            (reservation.proposed_traject.number_of_places or 0) - reservation.proposed_traject.confirmed_users.count()
        )

        if reservation.number_of_places > remaining_places:
            messages.error(request, "Pas assez de places restantes pour confirmer cette réservation.")
            return redirect('my_reservations')

        reservation.status = 'confirmed'
        reservation.save()

        reservation.proposed_traject.confirmed_users.add(reservation.user)

        if reservation.user.email:
            send_mail(
                subject="Votre réservation a été confirmée",
                message=(
                    f"Bonjour,\n\n"
                    f"Votre réservation pour le trajet "
                    f"{reservation.proposed_traject.traject.start_adress} → "
                    f"{reservation.proposed_traject.traject.end_adress} "
                    f"du {reservation.proposed_traject.date.strftime('%d/%m/%Y')} "
                    f"a été confirmée.\n\n"
                    "Connectez-vous à Bana pour voir les détails."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.user.email],
                fail_silently=True,
            )

        messages.success(request, "Réservation confirmée.")

    elif action == 'reject':
        reservation.status = 'canceled'
        reservation.save()

        if reservation.user.email:
            send_mail(
                subject="Votre réservation a été refusée",
                message=(
                    f"Bonjour,\n\n"
                    f"Votre réservation pour le trajet "
                    f"{reservation.proposed_traject.traject.start_adress} → "
                    f"{reservation.proposed_traject.traject.end_adress} "
                    f"du {reservation.proposed_traject.date.strftime('%d/%m/%Y')} "
                    f"a été refusée.\n\n"
                    "Connectez-vous à Bana pour consulter d'autres trajets."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reservation.user.email],
                fail_silently=True,
            )

        messages.success(request, "Réservation refusée.")

    return redirect('my_reservations')


@login_required
def auto_reserve(request, proposed_id, researched_id):
    proposed_traject = get_object_or_404(ProposedTraject, id=proposed_id, is_active=True)
    researched_traject = get_object_or_404(
        ResearchedTraject,
        id=researched_id,
        user=request.user,
        is_active=True
    )

    if proposed_traject.user == request.user:
        messages.error(request, "Vous ne pouvez pas réserver votre propre trajet.")
        return redirect('my_matchings_researched')

    existing = Reservation.objects.filter(
        user=request.user,
        proposed_traject=proposed_traject,
        researched_traject=researched_traject
    ).exclude(status="canceled").exists()

    if existing:
        messages.warning(request, "Vous avez déjà une réservation en cours pour cette date.")
        return redirect('my_reservations')

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
    trajet_info = f"{proposed_traject.traject.start_adress} → {proposed_traject.traject.end_adress}"

    send_mail(
        subject="Nouvelle demande de réservation reçue",
        message=(
            f"Bonjour,\n\n"
            f"Vous avez reçu une nouvelle demande de réservation.\n\n"
            f"Détails du trajet : {trajet_info}\n"
            f"Nombre d'enfant(s) demandé(s) : {requested_places}\n\n"
            "Connectez-vous à Bana pour accepter ou refuser la demande."
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

    # =========================
    # Réservations faites (parent)
    # =========================
    made_raw = (
        Reservation.objects
        .filter(user=user)
        .select_related(
            'proposed_traject', 'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject',
            'proposed_traject__user', 'proposed_traject__user__profile'
        )
        .exclude(status='canceled')
    )

    made_grouped = (
        made_raw
        .values(
            'researched_traject__groupe_uid',
            'proposed_traject__groupe_uid',
            'proposed_traject__user_id',
        )
        .annotate(
            first_date=Min('proposed_traject__date'),
            last_date=Max('proposed_traject__date'),
            count=Count('id'),
        )
        .order_by('-last_date')
    )

    made_reservations = []
    for item in made_grouped:
        header = (
            Reservation.objects
            .filter(
                user=user,
                researched_traject__groupe_uid=item['researched_traject__groupe_uid'],
                proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
                proposed_traject__user_id=item['proposed_traject__user_id'],
            )
            .select_related(
                'proposed_traject', 'researched_traject',
                'proposed_traject__traject', 'researched_traject__traject',
                'proposed_traject__user', 'proposed_traject__user__profile'
            )
            .first()
        )

        if not header:
            continue

        made_reservations.append({
            "header": header,
            "first_date": item["first_date"],
            "last_date": item["last_date"],
            "count": item["count"],
        })

    # =========================
    # Réservations reçues (yaya)
    # =========================
    received_raw = (
        Reservation.objects
        .filter(proposed_traject__user=user)
        .select_related(
            'user', 'user__profile',
            'proposed_traject', 'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject'
        )
        .exclude(status='canceled')
    )

    received_grouped = (
        received_raw
        .values(
            'proposed_traject__groupe_uid',
            'researched_traject__groupe_uid',
            'user_id',
        )
        .annotate(
            first_date=Min('researched_traject__date'),
            last_date=Max('researched_traject__date'),
            count=Count('id'),
        )
        .order_by('-last_date')
    )

    received_reservations = []
    for item in received_grouped:
        header = (
            Reservation.objects
            .filter(
                proposed_traject__user=user,
                proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
                researched_traject__groupe_uid=item['researched_traject__groupe_uid'],
                user_id=item['user_id'],
            )
            .select_related(
                'user', 'user__profile',
                'proposed_traject', 'researched_traject',
                'proposed_traject__traject', 'researched_traject__traject'
            )
            .first()
        )

        if not header:
            continue

        received_reservations.append({
            "header": header,
            "first_date": item["first_date"],
            "last_date": item["last_date"],
            "count": item["count"],
        })

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
        return redirect('my_matchings_simple')
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
            "Connectez-vous à Bana pour consulter les trajets disponible et effectuer une réservation. https://www.bana.mobi/trajets/recherches/matchings/"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[parent_email],
        fail_silently=False,
    )

    messages.success(request, "Votre aide a été proposée et le parent a été informé par email.")
    return redirect('my_matchings_simple')


@login_required
def my_reservations_made_detail(request, researched_groupe_uid, proposed_groupe_uid, yaya_user_id):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    reservations_qs = (
        Reservation.objects
        .filter(
            user=user,
            researched_traject__groupe_uid=researched_groupe_uid,
            proposed_traject__groupe_uid=proposed_groupe_uid,
            proposed_traject__user_id=yaya_user_id,
        )
        .select_related(
            'user', 'user__profile',
            'proposed_traject', 'proposed_traject__user', 'proposed_traject__user__profile',
            'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject'
        )
        .prefetch_related(
            'researched_traject__children',
            'proposed_traject__transport_modes'
        )
        .order_by('proposed_traject__date', 'proposed_traject__departure_time')
    )

    header = reservations_qs.first()
    if not header:
        messages.error(request, "Réservations introuvables.")
        return redirect('my_reservations')

    stats = reservations_qs.aggregate(
        first_date=Min('proposed_traject__date'),
        last_date=Max('proposed_traject__date'),
        count=Count('id')
    )

    rows = []
    for r in reservations_qs:
        remaining_places = max(
            0,
            (r.proposed_traject.number_of_places or 0) - r.proposed_traject.confirmed_users.count()
        )

        rows.append({
            "reservation": r,
            "proposal": r.proposed_traject,
            "research": r.researched_traject,
            "remaining_places": remaining_places,
        })

    return render(request, 'trajects/my_reservations_made_detail.html', {
        'header': header,
        'stats': stats,
        'rows': rows,
        'is_abonned': is_abonned,
    })


@login_required
def my_reservations_received_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    reservations_qs = (
        Reservation.objects
        .filter(
            proposed_traject__user=user,
            proposed_traject__groupe_uid=proposed_groupe_uid,
            researched_traject__groupe_uid=researched_groupe_uid,
            user_id=parent_user_id,
        )
        .select_related(
            'user', 'user__profile',
            'proposed_traject', 'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject'
        )
        .prefetch_related(
            'researched_traject__children',
            'researched_traject__transport_modes',
            'proposed_traject__transport_modes'
        )
        .order_by('researched_traject__date', 'researched_traject__departure_time')
    )

    header = reservations_qs.first()
    if not header:
        messages.error(request, "Demandes introuvables.")
        return redirect('my_reservations')

    stats = reservations_qs.aggregate(
        first_date=Min('researched_traject__date'),
        last_date=Max('researched_traject__date'),
        count=Count('id')
    )

    rows = []
    for r in reservations_qs:
        remaining_places = max(
            0,
            (r.proposed_traject.number_of_places or 0) - r.proposed_traject.confirmed_users.count()
        )

        rows.append({
            "reservation": r,
            "proposal": r.proposed_traject,
            "research": r.researched_traject,
            "remaining_places": remaining_places,
        })

    return render(request, 'trajects/my_reservations_received_detail.html', {
        'header': header,
        'stats': stats,
        'rows': rows,
        'is_abonned': is_abonned,
    })

