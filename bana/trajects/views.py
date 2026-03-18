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
    """
    Places restantes = number_of_places.
    On considère que number_of_places est déjà décrémenté
    lors des confirmations de réservation.
    """
    try:
        return max(0, int(proposal.number_of_places or 0))
    except (TypeError, ValueError):
        return 0

def _normalized_service(user):
    service = getattr(getattr(user, "profile", None), "service", None)
    if not service:
        return None
    return str(service).strip().lower()

def get_matching_source_type(obj):
    """
    Détermine le type métier de l'objet source.
    """
    service = _normalized_service(obj.user)

    if isinstance(obj, ResearchedTraject):
        return "parent_research"

    if isinstance(obj, ProposedTraject):
        if obj.is_simple:
            return "yaya_simple"
        if service == "yaya":
            return "yaya_proposed"
        if service == "parent":
            return "parent_proposed"

    return None


def _time_ok(t1, t2, tolerance_minutes=45):
    """
    Compare deux heures avec une tolérance.
    Si une heure manque, on laisse passer.
    """
    if not t1 or not t2:
        return True

    tolerance = timedelta(minutes=tolerance_minutes)
    dt1 = datetime.combine(date.today(), t1)
    dt2 = datetime.combine(date.today(), t2)

    return (dt1 - tolerance) <= dt2 <= (dt1 + tolerance)


def _same_transport_mode(obj_modes_ids, other_modes_ids):
    return bool(set(obj_modes_ids).intersection(set(other_modes_ids)))


def _has_enough_places(proposal, researched):
    """
    Vérifie que le trajet proposé possède assez de places
    pour le nombre d'enfants liés à la recherche.
    """
    required_places = max(1, researched.children.count())
    return _available_places(proposal) >= required_places


def find_matches_for_parent_research(research, default_radius_km=5, time_tolerance_minutes=45):
    """
    Parent researched => match avec :
    - yaya proposed (A -> B)
    - yaya simple rayon
    - parent proposed (A -> B)
    """
    print("\n==============================")
    print("DEBUG PARENT RESEARCH:", research.id, research.date)
    print("Research user:", research.user.id, _normalized_service(research.user))
    print("Research start_point:", bool(research.traject and research.traject.start_point))
    print("Research end_point:", bool(research.traject and research.traject.end_point))
    print("Research departure:", research.departure_time)
    print("Research arrival:", research.arrival_time)
    print("Research transport_modes:", list(research.transport_modes.values_list("id", flat=True)))
    print("==============================")

    if not research.traject or not research.traject.start_point:
        print("STOP: research sans start_point")
        return []

    research_mode_ids = list(research.transport_modes.values_list("id", flat=True))

    base_qs = (
        ProposedTraject.objects
        .filter(date=research.date, is_active=True)
        .exclude(user=research.user)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .annotate(distance_start=Distance("traject__start_point", research.traject.start_point))
        .filter(distance_start__lte=D(km=50))
    )

    print("DEBUG base_qs count:", base_qs.count())

    valid_pks = []

    for proposal in base_qs:
        print("\n--- Proposal candidate ---")
        print("Proposal id:", proposal.id)
        print("Proposal user:", proposal.user.id, _normalized_service(proposal.user))
        print("Proposal is_simple:", proposal.is_simple)
        print("Proposal start_point:", bool(proposal.traject and proposal.traject.start_point))
        print("Proposal end_point:", bool(proposal.traject and proposal.traject.end_point))
        print("Proposal departure:", proposal.departure_time)
        print("Proposal arrival:", proposal.arrival_time)
        print("Proposal places:", proposal.number_of_places)
        print("Proposal transport_modes:", list(proposal.transport_modes.values_list("id", flat=True)))

        if not proposal.traject or not proposal.traject.start_point:
            print("SKIP: proposal sans start_point")
            continue

        proposal_service = _normalized_service(proposal.user)

        if proposal.is_simple and proposal_service != "yaya":
            print("SKIP: proposal simple mais user non yaya")
            continue

        if not proposal.is_simple and proposal_service not in ["yaya", "parent"]:
            print("SKIP: proposal précise avec service invalide")
            continue

        start_distance_m = (
            proposal.distance_start.m
            if proposal.distance_start is not None
            else proposal.traject.start_point.distance(research.traject.start_point)
        )

        allowed_radius_km = proposal.search_radius_km if proposal.is_simple else default_radius_km
        print("Start distance (m):", start_distance_m)
        print("Allowed radius (m):", D(km=allowed_radius_km).m)

        if start_distance_m > D(km=allowed_radius_km).m:
            print("SKIP: distance départ trop grande")
            continue

        proposal_mode_ids = list(proposal.transport_modes.values_list("id", flat=True))
        if not _same_transport_mode(research_mode_ids, proposal_mode_ids):
            print("SKIP: aucun mode de transport commun")
            continue

        enough_places = _has_enough_places(proposal, research)
        print("Enough places:", enough_places)
        if not enough_places:
            print("SKIP: pas assez de places")
            continue

        if proposal.is_simple:
            print("MATCH: simple proposal validée")
            valid_pks.append(proposal.pk)
            continue

        if not (research.traject.end_point and proposal.traject.end_point):
            print("SKIP: end_point manquant")
            continue

        end_distance_m = research.traject.end_point.distance(proposal.traject.end_point)
        print("End distance (raw):", end_distance_m)

        if end_distance_m > D(km=default_radius_km).m:
            print("SKIP: distance arrivée trop grande")
            continue

        dep_ok = _time_ok(research.departure_time, proposal.departure_time, time_tolerance_minutes)
        arr_ok = _time_ok(research.arrival_time, proposal.arrival_time, time_tolerance_minutes)
        print("Departure time OK:", dep_ok)
        print("Arrival time OK:", arr_ok)

        if not dep_ok:
            print("SKIP: heure départ incompatible")
            continue

        if not arr_ok:
            print("SKIP: heure arrivée incompatible")
            continue

        print("MATCH: precise proposal validée")
        valid_pks.append(proposal.pk)

    print("DEBUG valid_pks:", valid_pks)

    return list(
        ProposedTraject.objects
        .filter(pk__in=valid_pks)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .order_by("date", "departure_time")
    )

def find_matches_for_precise_offer(proposal, default_radius_km=5, time_tolerance_minutes=45):
    """
    Offre précise (parent ou yaya) => match avec parent researched.
    """
    print("\n==============================")
    print("DEBUG PRECISE OFFER:", proposal.id, proposal.date)
    print("Proposal user:", proposal.user.id, _normalized_service(proposal.user))
    print("Proposal is_simple:", proposal.is_simple)
    print("Proposal start_point:", bool(proposal.traject and proposal.traject.start_point))
    print("Proposal end_point:", bool(proposal.traject and proposal.traject.end_point))
    print("Proposal departure:", proposal.departure_time)
    print("Proposal arrival:", proposal.arrival_time)
    print("Proposal places:", proposal.number_of_places)
    print("Proposal transport_modes:", list(proposal.transport_modes.values_list("id", flat=True)))
    print("==============================")

    if not proposal.traject or not proposal.traject.start_point:
        print("STOP: proposal sans start_point")
        return []

    proposal_mode_ids = list(proposal.transport_modes.values_list("id", flat=True))

    base_qs = (
        ResearchedTraject.objects
        .filter(date=proposal.date, is_active=True)
        .exclude(user=proposal.user)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children")
        .annotate(distance_start=Distance("traject__start_point", proposal.traject.start_point))
        .filter(distance_start__lte=D(km=50))
    )

    print("DEBUG base_qs count:", base_qs.count())

    valid_pks = []

    for research in base_qs:
        print("\n--- Research candidate ---")
        print("Research id:", research.id)
        print("Research user:", research.user.id, _normalized_service(research.user))
        print("Research start_point:", bool(research.traject and research.traject.start_point))
        print("Research end_point:", bool(research.traject and research.traject.end_point))
        print("Research departure:", research.departure_time)
        print("Research arrival:", research.arrival_time)
        print("Research children_count:", research.children.count())
        print("Research transport_modes:", list(research.transport_modes.values_list("id", flat=True)))

        research_service = _normalized_service(research.user)
        if research_service != "parent":
            print("SKIP: research user non parent")
            continue

        if not research.traject or not research.traject.start_point:
            print("SKIP: research sans start_point")
            continue

        start_distance_m = (
            research.distance_start.m
            if research.distance_start is not None
            else research.traject.start_point.distance(proposal.traject.start_point)
        )
        print("Start distance (m):", start_distance_m)
        print("Allowed radius (m):", D(km=default_radius_km).m)

        if start_distance_m > D(km=default_radius_km).m:
            print("SKIP: distance départ trop grande")
            continue

        research_mode_ids = list(research.transport_modes.values_list("id", flat=True))
        if not _same_transport_mode(proposal_mode_ids, research_mode_ids):
            print("SKIP: aucun mode de transport commun")
            continue

        enough_places = _has_enough_places(proposal, research)
        print("Enough places:", enough_places)
        if not enough_places:
            print("SKIP: pas assez de places")
            continue

        if not (proposal.traject.end_point and research.traject.end_point):
            print("SKIP: end_point manquant")
            continue

        end_distance_m = proposal.traject.end_point.distance(research.traject.end_point)
        print("End distance (raw):", end_distance_m)

        if end_distance_m > D(km=default_radius_km).m:
            print("SKIP: distance arrivée trop grande")
            continue

        dep_ok = _time_ok(proposal.departure_time, research.departure_time, time_tolerance_minutes)
        arr_ok = _time_ok(proposal.arrival_time, research.arrival_time, time_tolerance_minutes)
        print("Departure time OK:", dep_ok)
        print("Arrival time OK:", arr_ok)

        if not dep_ok:
            print("SKIP: heure départ incompatible")
            continue

        if not arr_ok:
            print("SKIP: heure arrivée incompatible")
            continue

        print("MATCH: precise research validée")
        valid_pks.append(research.pk)

    print("DEBUG valid_pks:", valid_pks)

    return list(
        ResearchedTraject.objects
        .filter(pk__in=valid_pks)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children")
        .order_by("date", "departure_time")
    )
    
def find_matches_for_simple_offer(simple_proposal, time_tolerance_minutes=45):
    """
    Yaya simple rayon => match avec parent researched.
    Ici on ne vérifie pas le point B.
    """
    print("\n==============================")
    print("DEBUG SIMPLE OFFER:", simple_proposal.id, simple_proposal.date)
    print("Simple proposal user:", simple_proposal.user.id, _normalized_service(simple_proposal.user))
    print("Simple proposal start_point:", bool(simple_proposal.traject and simple_proposal.traject.start_point))
    print("Simple proposal radius:", simple_proposal.search_radius_km)
    print("Simple proposal places:", simple_proposal.number_of_places)
    print("Simple proposal transport_modes:", list(simple_proposal.transport_modes.values_list("id", flat=True)))
    print("==============================")

    if not simple_proposal.traject or not simple_proposal.traject.start_point:
        print("STOP: simple proposal sans start_point")
        return []

    proposal_mode_ids = list(simple_proposal.transport_modes.values_list("id", flat=True))
    allowed_radius_km = simple_proposal.search_radius_km or 5

    base_qs = (
        ResearchedTraject.objects
        .filter(date=simple_proposal.date, is_active=True)
        .exclude(user=simple_proposal.user)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children")
        .annotate(distance_start=Distance("traject__start_point", simple_proposal.traject.start_point))
        .filter(distance_start__lte=D(km=max(allowed_radius_km, 50)))
    )

    print("DEBUG base_qs count:", base_qs.count())

    valid_pks = []

    for research in base_qs:
        print("\n--- Research candidate ---")
        print("Research id:", research.id)
        print("Research user:", research.user.id, _normalized_service(research.user))
        print("Research start_point:", bool(research.traject and research.traject.start_point))
        print("Research children_count:", research.children.count())
        print("Research transport_modes:", list(research.transport_modes.values_list("id", flat=True)))

        research_service = _normalized_service(research.user)
        if research_service != "parent":
            print("SKIP: research user non parent")
            continue

        if not research.traject or not research.traject.start_point:
            print("SKIP: research sans start_point")
            continue

        start_distance_m = (
            research.distance_start.m
            if research.distance_start is not None
            else research.traject.start_point.distance(simple_proposal.traject.start_point)
        )

        print("Start distance (m):", start_distance_m)
        print("Allowed radius (m):", D(km=allowed_radius_km).m)

        if start_distance_m > D(km=allowed_radius_km).m:
            print("SKIP: distance départ trop grande")
            continue

        research_mode_ids = list(research.transport_modes.values_list("id", flat=True))
        if not _same_transport_mode(proposal_mode_ids, research_mode_ids):
            print("SKIP: aucun mode de transport commun")
            continue

        enough_places = _has_enough_places(simple_proposal, research)
        print("Enough places:", enough_places)
        if not enough_places:
            print("SKIP: pas assez de places")
            continue

        print("MATCH: simple research validée")
        valid_pks.append(research.pk)

    print("DEBUG valid_pks:", valid_pks)

    return list(
        ResearchedTraject.objects
        .filter(pk__in=valid_pks)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children")
        .order_by("date", "departure_time")
    )
    
def find_matching_trajects(obj, default_radius_km=5, time_tolerance_minutes=45):
    """
    Routeur métier principal.
    """
    source_type = get_matching_source_type(obj)

    if source_type == "parent_research":
        return find_matches_for_parent_research(
            obj,
            default_radius_km=default_radius_km,
            time_tolerance_minutes=time_tolerance_minutes,
        )

    if source_type in ["yaya_proposed", "parent_proposed"]:
        return find_matches_for_precise_offer(
            obj,
            default_radius_km=default_radius_km,
            time_tolerance_minutes=time_tolerance_minutes,
        )

    if source_type == "yaya_simple":
        return find_matches_for_simple_offer(
            obj,
            time_tolerance_minutes=time_tolerance_minutes,
        )

    return []

# ============================
#  Vues création de trajets
# ============================

@login_required
def proposed_traject(request, researchesTraject_id=None):
    """
    Création d'un trajet proposé précis A -> B
    pour parent ou yaya.
    """
    if request.method == "POST":
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)

        groupe_name = (request.POST.get("groupe_name") or "").strip() or "Mon trajet"
        groupe_uid = uuid.uuid4()

        proposed_trajects, success = save_proposed_traject(
            request,
            traject_form,
            proposed_form,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if success:
            created_count = len(proposed_trajects or [])
            total_matches = sum(len(find_matching_trajects(p)) for p in proposed_trajects)
            matched_any = total_matches > 0

            if matched_any:
                messages.success(
                    request,
                    f"{created_count} proposition(s) enregistrée(s) avec {total_matches} matching(s) trouvés."
                )
                return redirect("my_matchings_proposed")

            messages.warning(
                request,
                f"{created_count} proposition(s) enregistrée(s), mais aucun matching trouvé."
            )
            return redirect("my_proposed_trajects")

        messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        traject_form = TrajectForm()
        proposed_form = ProposedTrajectForm()

    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address", "place_id")
    )

    return render(request, "trajects/proposed_traject.html", {
        "traject_form": traject_form,
        "proposed_form": proposed_form,
        "researched_traject": researchesTraject_id,
        "fav_addresses": fav_addresses,
        "days_of_week": [
            ("1", "Lundi"), ("2", "Mardi"), ("3", "Mercredi"),
            ("4", "Jeudi"), ("5", "Vendredi"), ("6", "Samedi"), ("7", "Dimanche"),
        ],
    }) 

@login_required
def simple_proposed_traject(request):
    """
    Création d'un trajet simple rayon (Yaya).
    """
    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address", "place_id")
    )

    if request.method == "POST":
        form = SimpleProposedTrajectForm(request.POST)

        if form.is_valid():
            groupe_name = (request.POST.get("groupe_name") or "").strip() or "Mon trajet"
            groupe_uid = uuid.uuid4()

            proposed_trajects, success = save_simple_proposed_traject(
                request,
                form,
                groupe_name=groupe_name,
                groupe_uid=groupe_uid,
            )

            if success:
                created_count = len(proposed_trajects or [])
                total_matches = sum(len(find_matching_trajects(p)) for p in proposed_trajects)
                matched_any = total_matches > 0

                if matched_any:
                    messages.success(
                        request,
                        f"{created_count} trajet(s) simplifié(s) enregistré(s) avec {total_matches} matching(s) trouvés."
                    )
                    return redirect("my_matchings_simple")

                messages.warning(
                    request,
                    f"{created_count} trajet(s) simplifié(s) enregistré(s), mais aucun matching trouvé."
                )
                return redirect("my_simple_trajects")

            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = SimpleProposedTrajectForm()

    return render(request, "trajects/simple_proposed_traject.html", {
        "form": form,
        "days_of_week": [
            ("1", "Lundi"), ("2", "Mardi"), ("3", "Mercredi"),
            ("4", "Jeudi"), ("5", "Vendredi"), ("6", "Samedi"), ("7", "Dimanche"),
        ],
        "tr_weekdays": request.POST.getlist("tr_weekdays") if request.method == "POST" else [],
        "fav_addresses": fav_addresses,
    })

@login_required
def researched_traject(request):
    """
    Création d'une recherche parent.
    """
    transport_modes = TransportMode.objects.all()
    service = getattr(request.user.profile, "service", None)

    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address", "place_id")
    )

    if request.method == "POST":
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)

        groupe_name = (request.POST.get("groupe_name") or "").strip() or "Ma recherche"
        groupe_uid = uuid.uuid4()

        researched_trajects, success = save_researched_traject(
            request,
            traject_form,
            researched_form,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if success:
            created_count = len(researched_trajects or [])
            total_matches = sum(len(find_matching_trajects(r)) for r in researched_trajects)
            matched_any = total_matches > 0

            if matched_any:
                messages.success(
                    request,
                    f"{created_count} recherche(s) enregistrée(s) avec {total_matches} matching(s) trouvés."
                )
                return redirect("my_matchings_researched")

            messages.warning(
                request,
                f"{created_count} recherche(s) enregistrée(s), mais aucun matching trouvé."
            )
            return redirect("my_researched_trajects")

        messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")

        return render(request, "trajects/searched_traject.html", {
            "traject_form": traject_form,
            "researched_form": researched_form,
            "transport_modes": transport_modes,
            "fav_addresses": fav_addresses,
            "days_of_week": [
                ("1", "Lundi"), ("2", "Mardi"), ("3", "Mercredi"),
                ("4", "Jeudi"), ("5", "Vendredi"), ("6", "Samedi"), ("7", "Dimanche"),
            ],
            "start_adress": request.POST.get("start_adress", ""),
            "end_adress": request.POST.get("end_adress", ""),
            "departure_time": request.POST.get("departure_time", ""),
            "arrival_time": request.POST.get("arrival_time", ""),
            "recurrence_type": request.POST.get("recurrence_type", ""),
            "tr_weekdays": request.POST.getlist("tr_weekdays"),
            "date_debut": request.POST.get("date_debut", ""),
            "date_fin": request.POST.get("date_fin", ""),
            "service": service,
        })

    traject_form = TrajectForm()
    researched_form = ResearchedTrajectForm(user=request.user)

    return render(request, "trajects/searched_traject.html", {
        "traject_form": traject_form,
        "researched_form": researched_form,
        "transport_modes": transport_modes,
        "fav_addresses": fav_addresses,
        "days_of_week": [
            ("1", "Lundi"), ("2", "Mardi"), ("3", "Mercredi"),
            ("4", "Jeudi"), ("5", "Vendredi"), ("6", "Samedi"), ("7", "Dimanche"),
        ],
        "service": service,
    })

def generate_recurrent_proposals(
    request,
    recurrent_dates,
    traject,
    departure_time,
    arrival_time,
    number_of_places,
    details,
    recurrence_type,
    recurrence_interval=None,
    recurrence_days=None,
    date_debut=None,
    date_fin=None,
    cleaned_data=None,
    groupe_name=None,
    groupe_uid=None,
):
    """
    Crée les objets ProposedTraject pour chaque date générée.

    Notes :
    - recurrence_interval est conservé uniquement pour compatibilité éventuelle,
      mais n'est plus utilisé comme vraie source métier.
    - one_week reste une récurrence valide, donc on garde recurrence_type,
      recurrence_days, date_debut et date_fin si fournis.
    """
    proposals = []
    cleaned_data = cleaned_data or {}

    transport_modes = cleaned_data.get("transport_modes")
    languages = cleaned_data.get("languages")

    for date_obj in recurrent_dates:
        proposed = ProposedTraject.objects.create(
            user=request.user,
            traject=traject,
            date=date_obj,
            departure_time=departure_time,
            arrival_time=arrival_time,
            number_of_places=number_of_places,
            details=details,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if transport_modes:
            proposed.transport_modes.set(transport_modes)

        if languages:
            proposed.languages.set(languages)

        proposals.append(proposed)

    return proposals

def generate_recurrent_researches(
    request,
    recurrent_dates,
    traject,
    departure_time,
    arrival_time,
    recurrence_type,
    recurrence_interval=None,
    recurrence_days=None,
    date_debut=None,
    date_fin=None,
    cleaned_data=None,
    groupe_name=None,
    groupe_uid=None,
):
    """
    Crée les objets ResearchedTraject pour chaque date générée.

    On garde les métadonnées de récurrence sur chaque occurrence
    pour conserver un comportement homogène avec ProposedTraject.
    """
    recurrent_researches = []
    cleaned_data = cleaned_data or {}

    transport_modes = cleaned_data.get("transport_modes")
    children = cleaned_data.get("children")

    for date_obj in recurrent_dates:
        researched = ResearchedTraject.objects.create(
            user=request.user,
            traject=traject,
            date=date_obj,
            departure_time=departure_time,
            arrival_time=arrival_time,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_days=recurrence_days,
            date_debut=date_debut,
            date_fin=date_fin,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if transport_modes:
            researched.transport_modes.set(transport_modes)

        if children:
            researched.children.set(children)

        recurrent_researches.append(researched)

    return recurrent_researches

def generate_recurrent_dates(
    date_debut, date_fin, recurrence_type, recurrence_interval=None, specific_days=None
):
    """
    Génère les dates récurrentes selon le type choisi.

    Convention des jours :
    1 = lundi
    2 = mardi
    3 = mercredi
    4 = jeudi
    5 = vendredi
    6 = samedi
    7 = dimanche
    """

    if not date_debut:
        return []

    if not date_fin:
        date_fin = date_debut

    if date_debut > date_fin:
        return []

    # Nettoyage / normalisation des jours sélectionnés
    if specific_days:
        selected_days = sorted(
            {
                int(day)
                for day in specific_days
                if str(day).isdigit() and 1 <= int(day) <= 7
            }
        )
    else:
        # Si aucun jour n'est fourni, on prend le jour de la date de début
        selected_days = [date_debut.weekday() + 1]

    dates = []

    # Cas : plage simple entre date_debut et date_fin
    if recurrence_type == "one_week":
        current = date_debut
        while current <= date_fin:
            if (current.weekday() + 1) in selected_days:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    # Cas : weekly / biweekly
    if recurrence_type == "weekly":
        step_days = 7
    elif recurrence_type == "biweekly":
        step_days = 14
    else:
        # Fallback propre si type inconnu
        return [date_debut]

    # Pour chaque jour demandé, on calcule directement les occurrences
    for target_day in selected_days:
        target_weekday_python = target_day - 1  # Python: lundi=0 ... dimanche=6
        delta_days = (target_weekday_python - date_debut.weekday()) % 7
        first_occurrence = date_debut + timedelta(days=delta_days)

        current = first_occurrence
        while current <= date_fin:
            dates.append(current)
            current += timedelta(days=step_days)

    return sorted(set(dates))

# ============================================================
# 💾 Enregistrement des trajets proposés et recherchés
# ============================================================

def save_proposed_traject(request, traject_form, proposed_form, groupe_name=None, groupe_uid=None):
    if not (traject_form.is_valid() and proposed_form.is_valid()):
        return None, False

    traject = traject_form.save(commit=False)

    print("DEBUG save_proposed_traject")
    print("start_place_id:", traject_form.cleaned_data.get("start_place_id"))
    print("end_place_id:", traject_form.cleaned_data.get("end_place_id"))

    for field in ["start_place_id", "end_place_id"]:
        place_id = traject_form.cleaned_data.get(field)
        print("FIELD:", field, "PLACE_ID:", place_id)

        if not place_id:
            continue

        details = get_place_details(place_id)
        print("DETAILS:", details)

        if "lat" in details and "lng" in details:
            point = Point(details["lng"], details["lat"], srid=4326)
            if field == "start_place_id":
                traject.start_point = point
            else:
                traject.end_point = point

    print("start_point before save:", traject.start_point)
    print("end_point before save:", traject.end_point)

    traject.save()

    cleaned = proposed_form.cleaned_data
    recurrence_type = cleaned.get("recurrence_type")
    date_debut = cleaned.get("date_debut")
    date_fin = cleaned.get("date_fin") or date_debut
    selected_days = cleaned.get("tr_weekdays") or []

    recurrence_days = "|" + "|".join(map(str, selected_days)) + "|" if selected_days else None

    groupe_name = (groupe_name or "").strip() or "Mon trajet"
    groupe_uid = groupe_uid or uuid.uuid4()

    recurrent_dates = generate_recurrent_dates(
        date_debut=date_debut,
        date_fin=date_fin,
        recurrence_type=recurrence_type,
        specific_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    proposed_trajects = generate_recurrent_proposals(
        request=request,
        recurrent_dates=recurrent_dates,
        traject=traject,
        departure_time=cleaned.get("departure_time"),
        arrival_time=cleaned.get("arrival_time"),
        number_of_places=cleaned.get("number_of_places", 1),
        details=cleaned.get("details"),
        recurrence_type=recurrence_type,
        recurrence_interval=None,
        recurrence_days=recurrence_days,
        date_debut=date_debut,
        date_fin=date_fin,
        cleaned_data=cleaned,
        groupe_name=groupe_name,
        groupe_uid=groupe_uid,
    )

    return proposed_trajects, True

def save_researched_traject(request, traject_form, researched_form, groupe_name=None, groupe_uid=None):
    """Sauvegarde d’un trajet recherché (Parent)."""
    if not (traject_form.is_valid() and researched_form.is_valid()):
        return None, False

    traject = traject_form.save(commit=False)

    # DEBUG temporaire
    print("DEBUG save_researched_traject")
    print("start_place_id:", traject_form.cleaned_data.get("start_place_id"))
    print("end_place_id:", traject_form.cleaned_data.get("end_place_id"))

    for field in ["start_place_id", "end_place_id"]:
        place_id = traject_form.cleaned_data.get(field)
        print("FIELD:", field, "PLACE_ID:", place_id)

        if not place_id:
            continue

        details = get_place_details(place_id)
        print("DETAILS:", details)

        if "lat" in details and "lng" in details:
            point = Point(details["lng"], details["lat"], srid=4326)
            if field == "start_place_id":
                traject.start_point = point
            else:
                traject.end_point = point

    print("start_point before save:", traject.start_point)
    print("end_point before save:", traject.end_point)

    traject.save()

    cleaned = researched_form.cleaned_data
    recurrence_type = cleaned.get("recurrence_type")
    date_debut = cleaned.get("date_debut")
    date_fin = cleaned.get("date_fin") or date_debut
    selected_days = cleaned.get("tr_weekdays") or []

    recurrence_days = "|" + "|".join(map(str, selected_days)) + "|" if selected_days else None

    groupe_name = (groupe_name or "").strip() or "Ma recherche"
    groupe_uid = groupe_uid or uuid.uuid4()

    recurrent_dates = generate_recurrent_dates(
        date_debut=date_debut,
        date_fin=date_fin,
        recurrence_type=recurrence_type,
        specific_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    researched_trajects = generate_recurrent_researches(
        request=request,
        recurrent_dates=recurrent_dates,
        traject=traject,
        departure_time=cleaned.get("departure_time"),
        arrival_time=cleaned.get("arrival_time"),
        recurrence_type=recurrence_type,
        recurrence_interval=None,
        recurrence_days=recurrence_days,
        date_debut=date_debut,
        date_fin=date_fin,
        cleaned_data=cleaned,
        groupe_name=groupe_name,
        groupe_uid=groupe_uid,
    )

    return researched_trajects, True

def save_simple_proposed_traject(request, form, groupe_name=None, groupe_uid=None):
    if not form.is_valid():
        return None, False

    user = request.user
    cleaned = form.cleaned_data

    groupe_name = (groupe_name or "").strip() or "Mon trajet"
    groupe_uid = groupe_uid or uuid.uuid4()

    start_adress = cleaned.get("start_adress")
    transport_modes = cleaned.get("transport_modes")
    number_of_places = cleaned.get("number_of_places") or 1
    search_radius_km = cleaned.get("search_radius_km")

    recurrence_type = cleaned.get("recurrence_type")
    date_debut = cleaned.get("date_debut")
    date_fin = cleaned.get("date_fin") or date_debut
    selected_days = cleaned.get("tr_weekdays") or []

    recurrent_dates = generate_recurrent_dates(
        date_debut=date_debut,
        date_fin=date_fin,
        recurrence_type=recurrence_type,
        specific_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    traject = Traject.objects.create(
        start_adress=start_adress,
        end_adress=""
    )

    start_place_id = request.POST.get("start_place_id")
    print("DEBUG save_simple_proposed_traject start_place_id:", start_place_id)

    if start_place_id:
        start_details = get_place_details(start_place_id)
        print("DEBUG start_details:", start_details)

        if "lat" in start_details and "lng" in start_details:
            traject.start_point = Point(start_details["lng"], start_details["lat"], srid=4326)
            traject.save(update_fields=["start_point"])

    print("DEBUG simple traject start_point after save:", traject.start_point)

    proposed_trajects = []
    for date_obj in recurrent_dates:
        proposed = ProposedTraject.objects.create(
            user=user,
            traject=traject,
            date=date_obj,
            is_simple=True,
            number_of_places=number_of_places,
            search_radius_km=search_radius_km,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
            recurrence_type=recurrence_type,
            recurrence_interval=None,
            recurrence_days="|" + "|".join(map(str, selected_days)) + "|" if selected_days else None,
            date_debut=date_debut,
            date_fin=date_fin,
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
    
@login_required
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
# 🧭 VUES UTILISATEURS DETAIL 
# ============================================================

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
 
# ============================================================
# 🔵 Matching des trajets 
# ============================================================

@login_required
def my_matchings_proposed(request):
    """
    Proposed précis (parent ou yaya) -> match avec parent researched.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=False)
        .values("groupe_uid")
        .annotate(
            first_date=Min("date"),
            last_date=Max("date"),
            count=Count("id")
        )
        .order_by("-last_date")
    )

    headers = []
    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g["groupe_uid"])
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
            .order_by("date", "departure_time")
            .first()
        )
        if not header:
            continue

        matched_researches = []
        for proposal in (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g["groupe_uid"])
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
        ):
            matched_researches.extend(find_matching_trajects(proposal))

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            pair_map[key] = research
            
        if not pair_map:
            continue

        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
            "is_past": bool(g["last_date"] and g["last_date"] < today),
        })
    
    return render(request, "trajects/my_matchings_proposed.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })

@login_required
def my_matchings_simple(request):
    """
    Yaya simple rayon -> match avec parent researched.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=True)
        .values("groupe_uid")
        .annotate(
            first_date=Min("date"),
            last_date=Max("date"),
            count=Count("id")
        )
        .order_by("-last_date")
    )

    headers = []
    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=True, groupe_uid=g["groupe_uid"])
            .select_related("traject")
            .prefetch_related("transport_modes")
            .order_by("date", "departure_time")
            .first()
        )
        if not header:
            continue

        matched_researches = []
        for proposal in (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=True, groupe_uid=g["groupe_uid"])
            .select_related("traject")
            .prefetch_related("transport_modes")
        ):
            matched_researches.extend(find_matching_trajects(proposal))

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            pair_map[key] = research

        if not pair_map:
            continue
        
        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
            "is_past": bool(g["last_date"] and g["last_date"] < today),
        })

    return render(request, "trajects/my_matchings_simple.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })

@login_required
def my_matchings_researched(request):
    """
    Parent researched -> match avec :
    - yaya proposed
    - yaya simple rayon
    - parent proposed
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True)
        .values("groupe_uid")
        .annotate(
            first_date=Min("date"),
            last_date=Max("date"),
            count=Count("id")
        )
        .order_by("-last_date")
    )

    headers = []
    for g in groupes:
        header = (
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g["groupe_uid"])
            .select_related("traject")
            .prefetch_related("transport_modes", "children")
            .order_by("date", "departure_time")
            .first()
        )
        if not header:
            continue

        matched_proposals = []
        for research in (
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g["groupe_uid"])
            .select_related("traject")
            .prefetch_related("transport_modes", "children")
        ):
            matched_proposals.extend(find_matching_trajects(research))

        pair_map = {}
        for proposal in matched_proposals:
            key = (proposal.groupe_uid, proposal.user_id, proposal.is_simple)
            pair_map[key] = proposal

        if not pair_map:
            continue
        
        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
            "is_past": bool(g["last_date"] and g["last_date"] < today),
        })

    return render(request, "trajects/my_matchings_researched.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })
    
# ============================================================
# 🔵 MATCHINGS DES TRAJETS DETAIL
# ============================================================
   
@login_required
def my_matchings_proposed_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status="pending")
        .values_list("researched_traject_id", flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status="confirmed")
        .values_list("researched_traject_id", flat=True)
    )

    proposed_qs = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=False, groupe_uid=proposed_groupe_uid)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .order_by("date", "departure_time")
    )
    header = proposed_qs.first()
    if not header:
        return render(request, "trajects/my_matchings_proposed_detail.html", {
            "error": "Groupe proposé introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    researched_qs = (
        ResearchedTraject.objects
        .filter(user_id=parent_user_id, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )
    parent_header = researched_qs.first()
    if not parent_header:
        return render(request, "trajects/my_matchings_proposed_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned,
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    matched_researched_ids = set()
    for proposal in proposed_qs:
        matched = find_matching_trajects(proposal)
        matched_researched_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )

    proposed_by_date = {p.date: p for p in proposed_qs}

    rows = []
    for research in matched_dates_qs:
        proposal = proposed_by_date.get(research.date)
        rows.append({
            "research": research,
            "is_past": bool(research.date and research.date < today),
            "children_count": research.children.count(),
            "remaining_places": _available_places(proposal) if proposal else None,
        })

    return render(request, "trajects/my_matchings_proposed_detail.html", {
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
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    parent_pending_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status="pending")
        .values_list("researched_traject_id", flat=True)
    )
    parent_confirmed_ids = set(
        Reservation.objects.filter(proposed_traject__user=user, status="confirmed")
        .values_list("researched_traject_id", flat=True)
    )

    proposed_qs = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, is_simple=True, groupe_uid=proposed_groupe_uid)
        .select_related("traject")
        .prefetch_related("transport_modes")
        .order_by("date", "departure_time")
    )
    header = proposed_qs.first()
    if not header:
        return render(request, "trajects/my_matchings_simple_detail.html", {
            "error": "Groupe simple introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    researched_qs = (
        ResearchedTraject.objects
        .filter(user_id=parent_user_id, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )
    parent_header = researched_qs.first()
    if not parent_header:
        return render(request, "trajects/my_matchings_simple_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned,
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    matched_researched_ids = set()
    for proposal in proposed_qs:
        matched = find_matching_trajects(proposal)
        matched_researched_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )

    proposed_by_date = {p.date: p for p in proposed_qs}

    rows = []
    for research in matched_dates_qs:
        proposal = proposed_by_date.get(research.date)

        rows.append({
            "research": research,
            "is_past": bool(research.date and research.date < today),
            "children_count": research.children.count(),
            "remaining_places": _available_places(proposal) if proposal else None,
            "radius_km": proposal.search_radius_km if proposal else None,
            "transport_modes": proposal.transport_modes.all() if proposal else [],
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
def my_matchings_researched_detail(request, researched_groupe_uid, proposed_groupe_uid, matched_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    researched_qs = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related("traject")
        .prefetch_related("transport_modes", "children")
        .order_by("date", "departure_time")
    )
    researched_header = researched_qs.first()
    if not researched_header:
        return render(request, "trajects/my_matchings_researched_detail.html", {
            "error": "Groupe de recherche introuvable.",
            "is_abonned": is_abonned,
        })

    researched_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    proposed_qs = (
        ProposedTraject.objects
        .filter(
            user_id=matched_user_id,
            is_active=True,
            groupe_uid=proposed_groupe_uid,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .order_by("date", "departure_time")
    )
    proposed_header = proposed_qs.first()
    if not proposed_header:
        return render(request, "trajects/my_matchings_researched_detail.html", {
            "researched_header": researched_header,
            "error": "Groupe proposé introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        count=Count("id")
    )

    matched_proposed_ids = set()
    for research in researched_qs:
        matched = find_matching_trajects(research)
        matched_proposed_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ProposedTraject.objects
        .filter(
            pk__in=matched_proposed_ids,
            user_id=matched_user_id,
            groupe_uid=proposed_groupe_uid,
            is_active=True,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .order_by("date", "departure_time")
    )

    proposed_by_date = {p.date: p for p in matched_dates_qs}

    # Réservations déjà faites par le parent connecté
    my_pending_keys = set(
        f"{proposal_id}_{research_id}"
        for proposal_id, research_id in Reservation.objects.filter(
            user=user,
            status="pending"
        ).values_list("proposed_traject_id", "researched_traject_id")
    )

    my_confirmed_keys = set(
        f"{proposal_id}_{research_id}"
        for proposal_id, research_id in Reservation.objects.filter(
            user=user,
            status="confirmed"
        ).values_list("proposed_traject_id", "researched_traject_id")
    )

    my_canceled_keys = set(
        f"{proposal_id}_{research_id}"
        for proposal_id, research_id in Reservation.objects.filter(
            user=user,
            status="canceled"
        ).values_list("proposed_traject_id", "researched_traject_id")
    )

    rows = []
    for research in researched_qs:
        proposal = proposed_by_date.get(research.date)
        if not proposal:
            continue

        reservation_key = f"{proposal.id}_{research.id}"

        print("DEBUG row reservation_key:", reservation_key)

        rows.append({
            "research": research,
            "proposal": proposal,
            "reservation_key": reservation_key,
            "is_past": bool(research.date and research.date < today),
            "children_count": research.children.count(),
            "remaining_places": _available_places(proposal),
            "is_simple": proposal.is_simple,
            "radius_km": proposal.search_radius_km if proposal.is_simple else None,
        })

    return render(request, "trajects/my_matchings_researched_detail.html", {
        "researched_header": researched_header,
        "researched_stats": researched_stats,
        "proposed_header": proposed_header,
        "proposed_stats": proposed_stats,
        "rows": rows,
        "my_pending_keys": my_pending_keys,
        "my_confirmed_keys": my_confirmed_keys,
        "my_canceled_keys": my_canceled_keys,
        "is_abonned": is_abonned,
        "today": today,
    })
    
# ============================================================
# TOUT LES TRAJETS
# ============================================================
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

# ============================================================
# SUPPRESSION TRAJET + GROUPE
# ============================================================

@login_required
@transaction.atomic
def delete_proposed_groupe(request, groupe_uid):
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect('my_proposed_trajects', groupe_uid=groupe_uid)

    qs = ProposedTraject.objects.filter(
        user=request.user,
        groupe_uid=groupe_uid,
        is_simple=False,
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
        groupe_uid=groupe_uid,
        is_simple=False,
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
    """
    Supprime tout un groupe de trajets simples.
    Sécurité :
    - POST uniquement
    - uniquement les trajets de l'utilisateur connecté
    - uniquement les ProposedTraject marqués is_simple=True
    """
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect('my_simple_trajects')

    qs = ProposedTraject.objects.filter(
        user=request.user,
        groupe_uid=groupe_uid,
        is_simple=True,
    )

    if not qs.exists():
        messages.error(request, "Groupe simple introuvable.")
        return redirect('my_simple_trajects')

    count = qs.count()
    qs.delete()

    messages.success(request, f"Groupe supprimé ({count} date(s)).")
    return redirect('my_simple_trajects')

@login_required
def delete_simple_traject(request, groupe_uid, pk):
    """
    Supprime une seule occurrence d’un trajet simple.
    Sécurité :
    - POST uniquement
    - uniquement les trajets simples de l'utilisateur connecté
    """
    trajet = get_object_or_404(
        ProposedTraject,
        pk=pk,
        user=request.user,
        groupe_uid=groupe_uid,
        is_simple=True,
    )

    if request.method == "POST":
        trajet.delete()
        messages.success(request, "La date du trajet simplifié a été supprimée.")
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

# ============================================================
# AUTOCIMPLETION GOOGLE PLACE
# ============================================================

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

def place_details_view(request):
    place_id = request.GET.get("place_id")
    if not place_id:
        return JsonResponse({"error": "Le paramètre 'place_id' est requis."}, status=400)

    details = get_place_details(place_id)

    if "error" in details:
        return JsonResponse(details, status=500)

    return JsonResponse(details, status=200)

# ============================================================
# RESERVATION
# ============================================================


@login_required
def manage_reservation(request, reservation_id, action):
    next_url = request.GET.get("next")
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "user",
            "user__profile",
            "proposed_traject",
            "proposed_traject__user",
            "researched_traject",
        ),
        id=reservation_id,
        proposed_traject__user=request.user,
    )

    # Sécurité : on n'accepte que deux actions possibles
    if action not in ["accept", "reject"]:
        messages.error(request, "Action invalide.")
        return redirect(next_url or "my_reservations")

    # =========================
    # ACCEPTATION
    # =========================
    if action == "accept":
        # Évite de reconfirmer une réservation déjà confirmée
        if reservation.status == "confirmed":
            messages.info(request, "Cette réservation est déjà confirmée.")
            return redirect(next_url or "my_reservations")

        # Évite de confirmer une réservation déjà annulée
        if reservation.status == "canceled":
            messages.warning(request, "Cette réservation a déjà été annulée.")
            return redirect(next_url or "my_reservations")

        # Nombre de places demandées par cette réservation
        requested_places = int(reservation.number_of_places or 0)

        if requested_places <= 0:
            messages.error(request, "Le nombre de places demandé est invalide.")
            return redirect(next_url or "my_reservations")

        # IMPORTANT :
        # _available_places() doit être la seule source de vérité pour savoir
        # combien de places sont encore disponibles sur le trajet proposé.
        remaining_places = _available_places(reservation.proposed_traject)

        if requested_places > remaining_places:
            messages.error(
                request,
                "Pas assez de places restantes pour confirmer cette réservation.",
            )
            return redirect(next_url or "my_reservations")

        # On confirme la réservation
        reservation.status = "confirmed"
        reservation.save(update_fields=["status"])

        # On garde éventuellement la relation utilisateur confirmé
        # si elle t'est utile ailleurs dans l'app
        reservation.proposed_traject.confirmed_users.add(reservation.user)

        # On décrémente le nombre de places restantes sur le trajet
        # seulement si chez toi number_of_places représente les places DISPONIBLES
        reservation.proposed_traject.number_of_places = (
            remaining_places - requested_places
        )
        reservation.proposed_traject.save(update_fields=["number_of_places"])

        # Envoi de mail si une adresse email existe
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
        return redirect(next_url or "my_reservations")

    # =========================
    # REFUS
    # =========================
    elif action == "reject":
        # Si déjà annulée, inutile de refaire l'action
        if reservation.status == "canceled":
            messages.info(request, "Cette réservation est déjà annulée.")
            return redirect(next_url or "my_reservations")

        # Si déjà confirmée, on évite de la refuser ici sans logique métier claire
        # car sinon il faudrait potentiellement remettre les places disponibles
        if reservation.status == "confirmed":
            messages.warning(
                request,
                "Cette réservation est déjà confirmée. "
            )
            return redirect(next_url or "my_reservations")

        reservation.status = "canceled"
        reservation.save(update_fields=["status"])

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
        return redirect(next_url or "my_reservations")

@login_required
def auto_reserve(request, proposed_id, researched_id):
    next_url = request.POST.get("next")
    proposed_traject = get_object_or_404(ProposedTraject, id=proposed_id, is_active=True)
    researched_traject = get_object_or_404(ResearchedTraject, id=researched_id, user=request.user, is_active=True)
    
    if proposed_traject.user == request.user:
        messages.error(request, "Vous ne pouvez pas réserver votre propre trajet.")
        return redirect(next_url or 'my_matchings_researched')

    existing = Reservation.objects.filter(
        user=request.user,
        proposed_traject=proposed_traject,
        researched_traject=researched_traject
    ).exclude(status="canceled").exists()

    if existing:
        messages.warning(request, "Vous avez déjà une réservation en cours pour cette date.")
        return redirect(next_url or 'my_matchings_researched')

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
    return redirect(next_url or 'my_matchings_researched')

@login_required
def propose_help(request, researched_id):
    research = get_object_or_404(ResearchedTraject, id=researched_id)
    next_url = request.POST.get("next")

    session_key = f"help_notified_{request.user.id}_{researched_id}"
    if request.session.get(session_key, False):
        messages.info(request, "Vous avez déjà signalé votre disponibilité pour ce trajet.")
        return redirect(next_url or 'my_matchings_proposed')
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
    return redirect(next_url or 'my_matchings_proposed')

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
        .prefetch_related(
            'researched_traject__children',
            'researched_traject__children__chld_languages',
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
            .prefetch_related(
                'researched_traject__children',
                'researched_traject__children__chld_languages',
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
        .prefetch_related(
            'researched_traject__children',
            'researched_traject__children__chld_languages',
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
            .prefetch_related(
                'researched_traject__children',
                'researched_traject__children__chld_languages',
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
def my_reservations_made_detail(
    request, researched_groupe_uid, proposed_groupe_uid, matched_user_id):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    reservations_qs = (
        Reservation.objects.filter(
            user=user,
            researched_traject__groupe_uid=researched_groupe_uid,
            proposed_traject__groupe_uid=proposed_groupe_uid,
            proposed_traject__user_id=matched_user_id,
        )
        .select_related(
            "user",
            "user__profile",
            "proposed_traject",
            "proposed_traject__user",
            "proposed_traject__user__profile",
            "researched_traject",
            "proposed_traject__traject",
            "researched_traject__traject",
        )
        .prefetch_related(
            "researched_traject__children", "proposed_traject__transport_modes"
        )
        .order_by("proposed_traject__date", "proposed_traject__departure_time")
    )

    header = reservations_qs.first()
    if not header:
        messages.error(request, "Réservations introuvables.")
        return redirect("my_reservations")

    stats = reservations_qs.aggregate(
        first_date=Min("proposed_traject__date"),
        last_date=Max("proposed_traject__date"),
        count=Count("id"),
    )

    rows = []
    for r in reservations_qs:
        # number_of_places du trajet proposé = places restantes
        # donc on ne resoustrait surtout pas confirmed_users.count()
        remaining_places = _available_places(r.proposed_traject)

        rows.append(
            {
                "reservation": r,
                "proposal": r.proposed_traject,
                "research": r.researched_traject,
                "remaining_places": remaining_places,
            }
        )

    return render(
        request,
        "trajects/my_reservations_made_detail.html",
        {
            "header": header,
            "stats": stats,
            "rows": rows,
            "is_abonned": is_abonned,
        },
    )

@login_required
def my_reservations_received_detail(
    request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    reservations_qs = (
        Reservation.objects.filter(
            proposed_traject__user=user,
            proposed_traject__groupe_uid=proposed_groupe_uid,
            researched_traject__groupe_uid=researched_groupe_uid,
            user_id=parent_user_id,
        )
        .select_related(
            "user",
            "user__profile",
            "proposed_traject",
            "researched_traject",
            "proposed_traject__traject",
            "researched_traject__traject",
        )
        .prefetch_related(
            "researched_traject__children",
            "researched_traject__transport_modes",
            "proposed_traject__transport_modes",
        )
        .order_by("researched_traject__date", "researched_traject__departure_time")
    )

    header = reservations_qs.first()
    if not header:
        messages.error(request, "Demandes introuvables.")
        return redirect("my_reservations")

    stats = reservations_qs.aggregate(
        first_date=Min("researched_traject__date"),
        last_date=Max("researched_traject__date"),
        count=Count("id"),
    )

    rows = []
    for r in reservations_qs:
        # Même logique :
        # number_of_places du ProposedTraject est déjà le stock restant
        remaining_places = _available_places(r.proposed_traject)

        rows.append(
            {
                "reservation": r,
                "proposal": r.proposed_traject,
                "research": r.researched_traject,
                "remaining_places": remaining_places,
            }
        )

    return render(
        request,
        "trajects/my_reservations_received_detail.html",
        {
            "header": header,
            "stats": stats,
            "rows": rows,
            "is_abonned": is_abonned,
        },
    )
