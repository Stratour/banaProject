import re
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utils.geocoding import get_autocomplete_suggestions, get_place_details
from django.conf import settings
from django.contrib import messages
from accounts.models import Child, FavoriteAddress
from stripe_sub.models import Subscription
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from .forms import TrajectForm, ProposedTrajectForm, ResearchedTrajectForm, SimpleProposedTrajectForm
from django.db.models import Q, Min, Max, Count, Case, When, DateField
from datetime import datetime, timedelta, date
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
import uuid
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model
from functools import wraps

User = get_user_model()


def name_required(view_func):
    """Bloque l'accès si le prénom ou le nom n'est pas renseigné.
    La CI vérifiée valide automatiquement le prénom/nom (Stripe Identity les met à jour)."""
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = request.user.profile
        has_name = bool(request.user.first_name and request.user.last_name)
        if not has_name and not profile.ci_is_verified:
            messages.warning(
                request,
                _("Veuillez renseigner votre prénom et votre nom avant d'accéder aux trajets."),
            )
            return redirect("accounts:profile_edit")
        return view_func(request, *args, **kwargs)
    return wrapper


def subscription_complete_required(view_func):
    """Réservé aux abonnés ayant complété CI + BVM + photo."""
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not Subscription.is_user_abonned(user):
            messages.warning(
                request,
                _("Vous devez être abonné pour effectuer cette action."),
            )
            return redirect("accounts:profile")
        profile = user.profile
        if not (profile.ci_is_verified and profile.document_bvm and profile.profile_picture):
            messages.warning(
                request,
                _("Veuillez compléter votre vérification (identité, BVM et photo) avant d'effectuer cette action."),
            )
            return redirect("accounts:profile")
        return view_func(request, *args, **kwargs)
    return wrapper

def _available_places(proposal):
    """Places restantes — number_of_places est décrémenté à chaque confirmation."""
    return max(0, proposal.number_of_places)

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
    Utilise .all() pour bénéficier du prefetch_related si disponible.
    """
    required_places = max(1, len(researched.children.all()))
    return _available_places(proposal) >= required_places


def _aggregate_groupes(queryset, today=None):
    """Regroupe un queryset par groupe_uid avec stats de dates.

    next_date = prochaine date à venir (>= today) pour ce groupe.
    Si None, toutes les occurrences sont passées.
    """
    _today = today or timezone.now().date()
    return (
        queryset
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            next_date=Min(Case(When(date__gte=_today, then='date'), output_field=DateField())),
            count=Count('id'),
        )
        .order_by('-last_date')
    )


def _collect_matches(queryset):
    """Collecte tous les matchings pour chaque objet d'un queryset."""
    results = []
    for obj in queryset:
        results.extend(find_matching_trajects(obj))
    return results


def _delete_groupe(request, model, filters, redirect_success, redirect_error):
    """Supprime un groupe entier. POST uniquement."""
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect(redirect_error)
    count, _ = model.objects.filter(user=request.user, **filters).delete()
    if not count:
        messages.error(request, "Groupe introuvable.")
        return redirect(redirect_success)
    messages.success(request, f"Groupe supprimé ({count} date(s)).")
    return redirect(redirect_success)


def _delete_single(request, model, filters, redirect_name, groupe_uid, success_msg):
    """Supprime une occurrence unique. POST uniquement."""
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect(redirect_name, groupe_uid=groupe_uid)
    obj = get_object_or_404(model, user=request.user, **filters)
    obj.delete()
    messages.success(request, success_msg)
    return redirect(redirect_name, groupe_uid=groupe_uid)


def _build_match_rows(matched_dates_qs, proposed_by_date, today, extra_fields_fn=None, skip_if_no_proposal=False):
    """Construit la liste de rows pour les vues de matching détail."""
    rows = []
    for research in matched_dates_qs:
        proposal = proposed_by_date.get(research.date)
        if skip_if_no_proposal and not proposal:
            continue
        row = {
            "research": research,
            "is_past": bool(research.date and research.date < today),
            "children_count": len(research.children.all()),
            "remaining_places": _available_places(proposal) if proposal else None,
        }
        if extra_fields_fn:
            row.update(extra_fields_fn(research, proposal))
        rows.append(row)
    return rows


def find_matches_for_parent_research(research, default_radius_km=5, time_tolerance_minutes=45):
    """
    Parent researched => match avec :
    - yaya proposed (A -> B)
    - yaya simple rayon
    - parent proposed (A -> B)
    """
    if not research.traject or not research.traject.start_point:
        return []

    research_mode_ids = [tm.id for tm in research.transport_modes.all()]
    required_places = max(1, research.children.count())

    base_qs = (
        ProposedTraject.objects
        .filter(date=research.date, is_active=True)
        .exclude(user=research.user)
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "languages")
        .annotate(distance_start=Distance("traject__start_point", research.traject.start_point))
        .filter(distance_start__lte=D(km=50))
    )

    valid_pks = []

    for proposal in base_qs:
        if not proposal.traject or not proposal.traject.start_point:
            continue

        proposal_service = _normalized_service(proposal.user)

        if proposal.is_simple and proposal_service != "yaya":
            continue

        if not proposal.is_simple and proposal_service not in ["yaya", "parent"]:
            continue

        start_distance_m = (
            proposal.distance_start.m
            if proposal.distance_start is not None
            else proposal.traject.start_point.distance(research.traject.start_point)
        )

        allowed_radius_km = proposal.search_radius_km if proposal.is_simple else default_radius_km

        if start_distance_m > D(km=allowed_radius_km).m:
            continue

        proposal_mode_ids = [tm.id for tm in proposal.transport_modes.all()]
        if not _same_transport_mode(research_mode_ids, proposal_mode_ids):
            continue

        if _available_places(proposal) < required_places:
            continue

        if proposal.is_simple:
            valid_pks.append(proposal.pk)
            continue

        if not (research.traject.end_point and proposal.traject.end_point):
            continue

        end_distance_m = research.traject.end_point.distance(proposal.traject.end_point)

        if end_distance_m > D(km=default_radius_km).m:
            continue

        if not _time_ok(research.departure_time, proposal.departure_time, time_tolerance_minutes):
            continue

        if not _time_ok(research.arrival_time, proposal.arrival_time, time_tolerance_minutes):
            continue

        valid_pks.append(proposal.pk)

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
    if not proposal.traject or not proposal.traject.start_point:
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

    valid_pks = []

    for research in base_qs:
        research_service = _normalized_service(research.user)
        if research_service != "parent":
            continue

        if not research.traject or not research.traject.start_point:
            continue

        start_distance_m = (
            research.distance_start.m
            if research.distance_start is not None
            else research.traject.start_point.distance(proposal.traject.start_point)
        )

        if start_distance_m > D(km=default_radius_km).m:
            continue

        research_mode_ids = [tm.id for tm in research.transport_modes.all()]
        if not _same_transport_mode(proposal_mode_ids, research_mode_ids):
            continue

        if not _has_enough_places(proposal, research):
            continue

        if not (proposal.traject.end_point and research.traject.end_point):
            continue

        end_distance_m = proposal.traject.end_point.distance(research.traject.end_point)

        if end_distance_m > D(km=default_radius_km).m:
            continue

        if not _time_ok(proposal.departure_time, research.departure_time, time_tolerance_minutes):
            continue

        if not _time_ok(proposal.arrival_time, research.arrival_time, time_tolerance_minutes):
            continue

        valid_pks.append(research.pk)

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
    if not simple_proposal.traject or not simple_proposal.traject.start_point:
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

    valid_pks = []

    for research in base_qs:
        research_service = _normalized_service(research.user)
        if research_service != "parent":
            continue

        if not research.traject or not research.traject.start_point:
            continue

        start_distance_m = (
            research.distance_start.m
            if research.distance_start is not None
            else research.traject.start_point.distance(simple_proposal.traject.start_point)
        )

        if start_distance_m > D(km=allowed_radius_km).m:
            continue

        research_mode_ids = [tm.id for tm in research.transport_modes.all()]
        if not _same_transport_mode(proposal_mode_ids, research_mode_ids):
            continue

        if not _has_enough_places(simple_proposal, research):
            continue

        valid_pks.append(research.pk)

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

@name_required
def proposed_traject(request, researchesTraject_id=None):
    """
    Création d'un trajet proposé précis A -> B
    pour parent ou yaya.
    """
    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address", "place_id")
    )

    context_base = {
        "researched_traject": researchesTraject_id,
        "fav_addresses": fav_addresses,
        "days_of_week": [
            ("1", _("Lundi")),
            ("2", _("Mardi")),
            ("3", _("Mercredi")),
            ("4", _("Jeudi")),
            ("5", _("Vendredi")),
            ("6", _("Samedi")),
            ("7", _("Dimanche")),
        ],
    }

    if request.method == "POST":
        traject_form = TrajectForm(request.POST)
        proposed_form = ProposedTrajectForm(request.POST)

        groupe_name = (request.POST.get("groupe_name") or "").strip() or "Mon trajet"
        groupe_uid = uuid.uuid4()

        proposed_trajects, success = save_proposed_traject(
            request=request,
            traject_form=traject_form,
            proposed_form=proposed_form,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if success:
            proposed_trajects = proposed_trajects or []
            created_count = len(proposed_trajects)
            total_matches = sum(len(find_matching_trajects(p)) for p in proposed_trajects)

            if total_matches > 0:
                messages.success(
                    request,
                    _("%(count)s proposition(s) enregistrée(s) avec %(matches)s matching(s) trouvé(s).") % {
                        "count": created_count,
                        "matches": total_matches,
                    }
                )
                return redirect("my_matchings_proposed")

            messages.warning(
                request,
                _("%(count)s proposition(s) enregistrée(s), mais aucun matching trouvé.") % {
                    "count": created_count,
                }
            )
            return redirect("my_proposed_trajects")

        messages.error(
            request,
            _("Veuillez corriger les erreurs dans le formulaire.")
        )

        return render(
            request,
            "trajects/proposition/creer.html",
            {
                **context_base,
                "traject_form": traject_form,
                "proposed_form": proposed_form,
                "tr_weekdays": request.POST.getlist("tr_weekdays"),
            },
        )

    traject_form = TrajectForm()
    proposed_form = ProposedTrajectForm()

    return render(
        request,
        "trajects/proposition/creer.html",
        {
            **context_base,
            "traject_form": traject_form,
            "proposed_form": proposed_form,
            "tr_weekdays": [],
        },
    )
    
@name_required
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
                request=request,
                form=form,
                groupe_name=groupe_name,
                groupe_uid=groupe_uid,
            )

            if success:
                proposed_trajects = proposed_trajects or []
                created_count = len(proposed_trajects)
                total_matches = sum(len(find_matching_trajects(p)) for p in proposed_trajects)

                if total_matches > 0:
                    messages.success(
                        request,
                        _("%(count)s trajet(s) simplifié(s) enregistré(s) avec %(matches)s matching(s) trouvé(s).") % {
                            "count": created_count,
                            "matches": total_matches,
                        }
                    )
                    return redirect("my_matchings_simple")

                messages.warning(
                    request,
                    _("%(count)s trajet(s) simplifié(s) enregistré(s), mais aucun matching trouvé.") % {
                        "count": created_count,
                    }
                )
                return redirect("my_simple_trajects")

            messages.error(
                request,
                _("Erreur lors de l’enregistrement du trajet. Veuillez corriger les champs.")
            )
        else:
            messages.error(
                request,
                _("Veuillez corriger les erreurs dans le formulaire.")
            )
    else:
        form = SimpleProposedTrajectForm()

    return render(
        request,
        "trajects/proposition_rayon/creer.html",
        {
            "form": form,
            "days_of_week": [
                ("1", _("Lundi")),
                ("2", _("Mardi")),
                ("3", _("Mercredi")),
                ("4", _("Jeudi")),
                ("5", _("Vendredi")),
                ("6", _("Samedi")),
                ("7", _("Dimanche")),
            ],
            "tr_weekdays": request.POST.getlist("tr_weekdays") if request.method == "POST" else [],
            "fav_addresses": fav_addresses,
        },
    )
    
@name_required
def researched_traject(request):
    """
    Création d'une recherche parent.
    """
    # Un Parent doit avoir au moins un enfant enregistré avant de créer une recherche
    if not request.user.children.exists():
        messages.warning(
            request,
            _("Vous devez d'abord ajouter un enfant avant de créer une recherche de trajet."),
        )
        return redirect(reverse("accounts:add_child") + "?next=" + reverse("researched_traject"))

    transport_modes = TransportMode.objects.all()
    service = getattr(request.user.profile, "service", None)

    fav_addresses = list(
        FavoriteAddress.objects
        .filter(user=request.user)
        .order_by("label", "address")
        .values("label", "address", "place_id")
    )

    context_base = {
        "transport_modes": transport_modes,
        "fav_addresses": fav_addresses,
        "days_of_week": [
            ("1", _("Lundi")), ("2", _("Mardi")), ("3", _("Mercredi")),
            ("4", _("Jeudi")), ("5", _("Vendredi")), ("6", _("Samedi")), ("7", _("Dimanche")),
        ],
        "service": service,
    }

    if request.method == "POST":
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)

        groupe_name = (request.POST.get("groupe_name") or "").strip() or "Ma recherche"
        groupe_uid = uuid.uuid4()

        researched_trajects, success = save_researched_traject(
            request=request,
            traject_form=traject_form,
            researched_form=researched_form,
            groupe_name=groupe_name,
            groupe_uid=groupe_uid,
        )

        if success:
            researched_trajects = researched_trajects or []
            created_count = len(researched_trajects)
            total_matches = sum(len(find_matching_trajects(r)) for r in researched_trajects)

            if total_matches > 0:
                messages.success(
                    request,
                    _("%(count)s recherche(s) enregistrée(s) avec %(matches)s matching(s) trouvé(s).") % {
                        "count": created_count,
                        "matches": total_matches,
                    }
                )
                return redirect("my_matchings_researched")

            messages.warning(
                request,
                _("%(count)s recherche(s) enregistrée(s), mais aucun matching trouvé.") % {
                    "count": created_count,
                }
            )
            return redirect("my_researched_trajects")

        messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))

        return render(
            request,
            "trajects/recherche/creer.html",
            {
                **context_base,
                "traject_form": traject_form,
                "researched_form": researched_form,
                "tr_weekdays": request.POST.getlist("tr_weekdays"),
            },
        )

    traject_form = TrajectForm()
    researched_form = ResearchedTrajectForm(user=request.user)

    return render(
        request,
        "trajects/recherche/creer.html",
        {
            **context_base,
            "traject_form": traject_form,
            "researched_form": researched_form,
            "tr_weekdays": [],
        },
    )
    
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

    for field in ["start_place_id", "end_place_id"]:
        place_id = traject_form.cleaned_data.get(field)

        if not place_id:
            continue

        details = get_place_details(place_id)

        if details and "lat" in details and "lng" in details:
            point = Point(details["lng"], details["lat"], srid=4326)
            if field == "start_place_id":
                traject.start_point = point
            else:
                traject.end_point = point

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

    for field in ["start_place_id", "end_place_id"]:
        place_id = traject_form.cleaned_data.get(field)

        if not place_id:
            continue

        details = get_place_details(place_id)

        if details and "lat" in details and "lng" in details:
            point = Point(details["lng"], details["lat"], srid=4326)
            if field == "start_place_id":
                traject.start_point = point
            else:
                traject.end_point = point

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
    start_place_id = cleaned.get("start_place_id")
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
        end_adress="",
        start_place_id=start_place_id or None,
    )

    if start_place_id:
        start_details = get_place_details(start_place_id)

        if start_details and "lat" in start_details and "lng" in start_details:
            traject.start_point = Point(
                start_details["lng"],
                start_details["lat"],
                srid=4326,
            )
            traject.save(update_fields=["start_point"])

    proposed_trajects = []

    recurrence_days_value = (
        "|" + "|".join(map(str, selected_days)) + "|"
        if selected_days else None
    )

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
            recurrence_days=recurrence_days_value,
            date_debut=date_debut,
            date_fin=date_fin,
        )
        proposed.transport_modes.set(transport_modes)
        proposed_trajects.append(proposed)

    return proposed_trajects, True

# ============================================================
# 🧭 VUES UTILISATEURS
# ============================================================

@name_required
def my_proposed_trajects(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    groupes = _aggregate_groupes(
        ProposedTraject.objects.filter(user=user, is_active=True, is_simple=False)
    )

    proposed_headers = []
    for g in groupes:
        header = (
            ProposedTraject.objects
            .filter(user=user, groupe_uid=g["groupe_uid"], is_active=True)
            .order_by("date", "departure_time")
            .first()
        )
        if not header:
            continue
        header.groupe_count = g["count"]
        header.groupe_first_date = g["first_date"]
        header.groupe_last_date = g["last_date"]
        proposed_headers.append(header)

    return render(request, "trajects/proposition/trajets_liste.html", {
        "proposed_trajects": proposed_headers,
        "is_abonned": is_abonned,
    })

@name_required
def my_simple_trajects(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)

    groupes = _aggregate_groupes(
        ProposedTraject.objects.filter(user=user, is_simple=True, is_active=True)
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

    return render(request, 'trajects/proposition_rayon/trajets_liste.html', {
        'simple_trajects': headers,
        'is_abonned': is_abonned,
    })
    
@name_required
def my_researched_trajects(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    
    groupes = _aggregate_groupes(
        ResearchedTraject.objects.filter(user=user, is_active=True)
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


    return render(request, 'trajects/recherche/trajets_liste.html', {
        'researched_trajects': researched_headers,
        'is_abonned': is_abonned,
    })

# ============================================================
# 🧭 VUES UTILISATEURS DETAIL 
# ============================================================

@name_required
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

    return render(request, 'trajects/proposition/trajet_detail.html', {
        'header': header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'is_abonned': is_abonned,
        'stats': stats,
        
    })
      
@name_required
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

    
    return render(request, 'trajects/proposition_rayon/trajet_detail.html', {
        'header': header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'stats': stats,
        'is_abonned': is_abonned,
    })
    
@name_required
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
    
    return render(request, 'trajects/recherche/trajet_detail.html', {
        'header': researched_header,
        'occurrences_upcoming': occurrences_upcoming,
        'occurrences_past': occurrences_past,
        'is_abonned': is_abonned,
        'stats': stats,
    })
 
# ============================================================
# 🔵 Matching des trajets 
# ============================================================

@name_required
def my_matchings_proposed(request):
    """
    Proposed précis (parent ou yaya) -> match avec parent researched.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = _aggregate_groupes(
        ProposedTraject.objects.filter(user=user, is_active=True, is_simple=False),
        today=today,
    )

    headers = []
    for g in groupes:
        if g["last_date"] and g["last_date"] < today:
            continue

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

        matched_researches = _collect_matches(
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
        )

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            if key not in pair_map:
                pair_map[key] = research
                research.matched_date_debut = research.date
                research.matched_date_fin = research.date
            else:
                existing = pair_map[key]
                if research.date:
                    existing.matched_date_debut = min(existing.matched_date_debut, research.date) if existing.matched_date_debut else research.date
                    existing.matched_date_fin = max(existing.matched_date_fin, research.date) if existing.matched_date_fin else research.date

        if not pair_map:
            continue

        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
        })

    return render(request, "trajects/proposition/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })

@name_required
def my_matchings_simple(request):
    """
    Yaya simple rayon -> match avec parent researched.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)

    groupes = _aggregate_groupes(
        ProposedTraject.objects.filter(user=user, is_active=True, is_simple=True),
        today=today,
    )

    headers = []
    for g in groupes:
        if g["last_date"] and g["last_date"] < today:
            continue

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

        matched_researches = _collect_matches(
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=True, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject")
            .prefetch_related("transport_modes")
        )

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            if key not in pair_map:
                pair_map[key] = research
                research.matched_date_debut = research.date
                research.matched_date_fin = research.date
            else:
                existing = pair_map[key]
                if research.date:
                    existing.matched_date_debut = min(existing.matched_date_debut, research.date) if existing.matched_date_debut else research.date
                    existing.matched_date_fin = max(existing.matched_date_fin, research.date) if existing.matched_date_fin else research.date

        if not pair_map:
            continue

        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
        })

    return render(request, "trajects/proposition_rayon/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })

@name_required
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

    groupes = _aggregate_groupes(
        ResearchedTraject.objects.filter(user=user, is_active=True),
        today=today,
    )

    headers = []
    for g in groupes:
        if g["last_date"] and g["last_date"] < today:
            continue

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

        matched_proposals = _collect_matches(
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject")
            .prefetch_related("transport_modes", "children")
        )

        pair_map = {}
        for proposal in matched_proposals:
            key = (proposal.groupe_uid, proposal.user_id, proposal.is_simple)
            if key not in pair_map:
                pair_map[key] = proposal
                proposal.matched_date_debut = proposal.date
                proposal.matched_date_fin = proposal.date
            else:
                existing = pair_map[key]
                if proposal.date:
                    existing.matched_date_debut = min(existing.matched_date_debut, proposal.date) if existing.matched_date_debut else proposal.date
                    existing.matched_date_fin = max(existing.matched_date_fin, proposal.date) if existing.matched_date_fin else proposal.date

        if not pair_map:
            continue

        headers.append({
            "header": header,
            "stats": g,
            "matches": list(pair_map.values()),
            "matches_count": len(pair_map),
        })

    return render(request, "trajects/recherche/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "today": today,
    })
    
# ============================================================
# 🔵 MATCHINGS DES TRAJETS DETAIL
# ============================================================
   
@name_required
def my_matchings_proposed_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

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
        return render(request, "trajects/proposition/matching_detail.html", {
            "error": "Groupe proposé introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
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
        return render(request, "trajects/proposition/matching_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned,
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
        count=Count("id")
    )

    matched_researched_ids = set()
    for proposal in proposed_qs.filter(date__gte=today):
        matched = find_matching_trajects(proposal)
        matched_researched_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True,
            date__gte=today,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )

    proposed_by_date = {p.date: p for p in proposed_qs.filter(date__gte=today)}
    rows = _build_match_rows(matched_dates_qs, proposed_by_date, today)
    matched_parent_stats = matched_dates_qs.aggregate(first_date=Min("date"), last_date=Max("date"))

    return render(request, "trajects/proposition/matching_detail.html", {
        "header": header,
        "proposed_stats": proposed_stats,
        "parent_header": parent_header,
        "parent_stats": parent_stats,
        "matched_parent_stats": matched_parent_stats,
        "rows": rows,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })

@name_required
def my_matchings_simple_detail(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

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
        return render(request, "trajects/proposition_rayon/matching_detail.html", {
            "error": "Groupe simple introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
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
        return render(request, "trajects/proposition_rayon/matching_detail.html", {
            "header": header,
            "error": "Groupe du parent introuvable.",
            "is_abonned": is_abonned,
        })

    parent_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
        count=Count("id")
    )

    matched_researched_ids = set()
    for proposal in proposed_qs.filter(date__gte=today):
        matched = find_matching_trajects(proposal)
        matched_researched_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ResearchedTraject.objects
        .filter(
            id__in=matched_researched_ids,
            user_id=parent_user_id,
            groupe_uid=researched_groupe_uid,
            is_active=True,
            date__gte=today,
        )
        .select_related("traject", "user", "user__profile")
        .prefetch_related("transport_modes", "children", "children__chld_languages")
        .order_by("date", "departure_time")
    )

    proposed_by_date = {p.date: p for p in proposed_qs.filter(date__gte=today)}
    rows = _build_match_rows(
        matched_dates_qs, proposed_by_date, today,
        extra_fields_fn=lambda _, proposal: {
            "radius_km": proposal.search_radius_km if proposal else None,
            "transport_modes": proposal.transport_modes.all() if proposal else [],
        },
    )
    matched_parent_stats = matched_dates_qs.aggregate(first_date=Min("date"), last_date=Max("date"))

    return render(request, "trajects/proposition_rayon/matching_detail.html", {
        "header": header,
        "proposed_stats": proposed_stats,
        "parent_header": parent_header,
        "parent_stats": parent_stats,
        "matched_parent_stats": matched_parent_stats,
        "rows": rows,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
        "today": today,
        "parent_pending_ids": parent_pending_ids,
        "parent_confirmed_ids": parent_confirmed_ids,
    })

@name_required
def my_matchings_researched_detail(request, researched_groupe_uid, proposed_groupe_uid, matched_user_id):
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

    researched_qs = (
        ResearchedTraject.objects
        .filter(user=user, is_active=True, groupe_uid=researched_groupe_uid)
        .select_related("traject")
        .prefetch_related("transport_modes", "children")
        .order_by("date", "departure_time")
    )
    researched_header = researched_qs.first()
    if not researched_header:
        return render(request, "trajects/recherche/matching_detail.html", {
            "error": "Groupe de recherche introuvable.",
            "is_abonned": is_abonned,
        })

    researched_stats = researched_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
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
        return render(request, "trajects/recherche/matching_detail.html", {
            "researched_header": researched_header,
            "error": "Groupe proposé introuvable.",
            "is_abonned": is_abonned,
        })

    proposed_stats = proposed_qs.aggregate(
        first_date=Min("date"),
        last_date=Max("date"),
        next_date=Min(Case(When(date__gte=today, then="date"), output_field=DateField())),
        count=Count("id")
    )

    matched_proposed_ids = set()
    for research in researched_qs.filter(date__gte=today):
        matched = find_matching_trajects(research)
        matched_proposed_ids.update([m.id for m in matched])

    matched_dates_qs = (
        ProposedTraject.objects
        .filter(
            pk__in=matched_proposed_ids,
            user_id=matched_user_id,
            groupe_uid=proposed_groupe_uid,
            is_active=True,
            date__gte=today,
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

    rows = _build_match_rows(
        researched_qs, proposed_by_date, today,
        skip_if_no_proposal=True,
        extra_fields_fn=lambda research, proposal: {
            "proposal": proposal,
            "reservation_key": f"{proposal.id}_{research.id}",
            "is_simple": proposal.is_simple,
            "radius_km": proposal.search_radius_km if proposal.is_simple else None,
        },
    )
    matched_proposed_stats = matched_dates_qs.aggregate(first_date=Min("date"), last_date=Max("date"))

    return render(request, "trajects/recherche/matching_detail.html", {
        "researched_header": researched_header,
        "researched_stats": researched_stats,
        "proposed_header": proposed_header,
        "proposed_stats": proposed_stats,
        "matched_proposed_stats": matched_proposed_stats,
        "rows": rows,
        "my_pending_keys": my_pending_keys,
        "my_confirmed_keys": my_confirmed_keys,
        "my_canceled_keys": my_canceled_keys,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
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
    return _delete_groupe(
        request, ProposedTraject,
        filters={"groupe_uid": groupe_uid, "is_simple": False},
        redirect_success="my_proposed_trajects",
        redirect_error="my_proposed_trajects",
    )

@login_required
def delete_proposed_traject(request, groupe_uid, pk):
    return _delete_single(
        request, ProposedTraject,
        filters={"pk": pk, "groupe_uid": groupe_uid, "is_simple": False},
        redirect_name="my_proposed_groupe_detail",
        groupe_uid=groupe_uid,
        success_msg="La date du trajet proposé a été supprimée.",
    )

@login_required
@transaction.atomic
def delete_simple_groupe(request, groupe_uid):
    return _delete_groupe(
        request, ProposedTraject,
        filters={"groupe_uid": groupe_uid, "is_simple": True},
        redirect_success="my_simple_trajects",
        redirect_error="my_simple_trajects",
    )

@login_required
def delete_simple_traject(request, groupe_uid, pk):
    return _delete_single(
        request, ProposedTraject,
        filters={"pk": pk, "groupe_uid": groupe_uid, "is_simple": True},
        redirect_name="my_simple_groupe_detail",
        groupe_uid=groupe_uid,
        success_msg="La date du trajet simplifié a été supprimée.",
    )

@login_required
def delete_researched_traject(request, groupe_uid, pk):
    return _delete_single(
        request, ResearchedTraject,
        filters={"pk": pk, "groupe_uid": groupe_uid},
        redirect_name="my_researched_groupe_detail",
        groupe_uid=groupe_uid,
        success_msg="La date du trajet recherché a été supprimée.",
    )

@login_required
@transaction.atomic
def delete_researched_groupe(request, groupe_uid):
    return _delete_groupe(
        request, ResearchedTraject,
        filters={"groupe_uid": groupe_uid},
        redirect_success="my_researched_trajects",
        redirect_error="my_researched_trajects",
    )



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


@subscription_complete_required
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

@subscription_complete_required
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

@subscription_complete_required
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

@name_required
def my_reservations(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = date.today()

    tab = request.GET.get('tab', 'active')
    if tab not in ('active', 'history'):
        tab = 'active'

    # =========================
    # Compteurs d'onglets (requêtes légères)
    # =========================
    active_count = (
        Reservation.objects.filter(user=user, proposed_traject__date__gte=today)
        .values('researched_traject__groupe_uid', 'proposed_traject__groupe_uid', 'proposed_traject__user_id')
        .distinct().count()
        + Reservation.objects.filter(proposed_traject__user=user, researched_traject__date__gte=today)
        .values('proposed_traject__groupe_uid')
        .distinct().count()
    )
    history_count = (
        Reservation.objects.filter(user=user, proposed_traject__date__lt=today)
        .values('researched_traject__groupe_uid', 'proposed_traject__groupe_uid', 'proposed_traject__user_id')
        .distinct().count()
        + Reservation.objects.filter(proposed_traject__user=user, researched_traject__date__lt=today)
        .values('proposed_traject__groupe_uid')
        .distinct().count()
    )

    # =========================
    # Groupement selon l'onglet
    # =========================
    if tab == 'active':
        # Groupes avec au moins une date future (tous statuts, y compris annulés)
        made_qs_filter = dict(user=user, proposed_traject__date__gte=today)
        made_exclude = {}
        made_date_field = 'proposed_traject__date'
        made_group_keys = ['researched_traject__groupe_uid', 'proposed_traject__groupe_uid', 'proposed_traject__user_id']
        made_header_filter = lambda item: dict(
            user=user,
            proposed_traject__date__gte=today,
            researched_traject__groupe_uid=item['researched_traject__groupe_uid'],
            proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
            proposed_traject__user_id=item['proposed_traject__user_id'],
        )

        received_qs_filter = dict(proposed_traject__user=user, researched_traject__date__gte=today)
        received_exclude = {}
        received_date_field = 'researched_traject__date'
        received_group_keys = ['proposed_traject__groupe_uid']
        received_header_filter = lambda item: dict(
            proposed_traject__user=user,
            proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
        )

        made_date_filter = {}
        received_date_filter = {}
    else:
        # Groupes avec au moins une date passée (tous statuts)
        made_qs_filter = dict(user=user, proposed_traject__date__lt=today)
        made_exclude = {}
        made_date_field = 'proposed_traject__date'
        made_group_keys = ['researched_traject__groupe_uid', 'proposed_traject__groupe_uid', 'proposed_traject__user_id']
        made_header_filter = lambda item: dict(
            user=user,
            proposed_traject__date__lt=today,
            researched_traject__groupe_uid=item['researched_traject__groupe_uid'],
            proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
            proposed_traject__user_id=item['proposed_traject__user_id'],
        )

        received_qs_filter = dict(proposed_traject__user=user, researched_traject__date__lt=today)
        received_exclude = {}
        received_date_field = 'researched_traject__date'
        received_group_keys = ['proposed_traject__groupe_uid']
        received_header_filter = lambda item: dict(
            proposed_traject__user=user,
            proposed_traject__groupe_uid=item['proposed_traject__groupe_uid'],
        )

        made_date_filter = {}
        received_date_filter = {}

    # =========================
    # Réservations faites (parent)
    # =========================
    made_base = (
        Reservation.objects.filter(**made_qs_filter)
        .select_related(
            'proposed_traject', 'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject',
            'proposed_traject__user', 'proposed_traject__user__profile'
        )
        .prefetch_related('researched_traject__children', 'researched_traject__children__chld_languages')
    )
    if made_exclude:
        made_base = made_base.exclude(**made_exclude)

    made_grouped = (
        made_base
        .values(*made_group_keys)
        .annotate(
            first_date=Min(made_date_field),
            last_date=Max(made_date_field),
            count=Count('id'),
        )
        .order_by('-last_date')
    )
    if made_date_filter:
        made_grouped = made_grouped.filter(**made_date_filter)

    made_reservations = []
    for item in made_grouped:
        header = (
            Reservation.objects
            .filter(**made_header_filter(item))
            .select_related(
                'proposed_traject', 'researched_traject',
                'proposed_traject__traject', 'researched_traject__traject',
                'proposed_traject__user', 'proposed_traject__user__profile'
            )
            .prefetch_related('researched_traject__children', 'researched_traject__children__chld_languages')
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
    received_base = (
        Reservation.objects.filter(**received_qs_filter)
        .select_related(
            'user', 'user__profile',
            'proposed_traject', 'researched_traject',
            'proposed_traject__traject', 'researched_traject__traject'
        )
        .prefetch_related('researched_traject__children', 'researched_traject__children__chld_languages')
    )
    if received_exclude:
        received_base = received_base.exclude(**received_exclude)

    received_grouped = (
        received_base
        .values(*received_group_keys)
        .annotate(
            first_date=Min(received_date_field),
            last_date=Max(received_date_field),
            count=Count('id'),
            requester_count=Count('user_id', distinct=True),
            pending_count=Count('id', filter=Q(status='pending')),
            full_dates_count=Count('proposed_traject', distinct=True, filter=Q(proposed_traject__number_of_places=0)),
            available_dates_count=Count('proposed_traject', distinct=True, filter=Q(proposed_traject__number_of_places__gt=0)),
        )
        .order_by('-last_date')
    )
    if received_date_filter:
        received_grouped = received_grouped.filter(**received_date_filter)

    received_reservations = []
    for item in received_grouped:
        header = (
            Reservation.objects
            .filter(**received_header_filter(item))
            .select_related(
                'user', 'user__profile',
                'proposed_traject', 'researched_traject',
                'proposed_traject__traject', 'researched_traject__traject'
            )
            .prefetch_related(
                'researched_traject__children', 'researched_traject__children__chld_languages',
                'proposed_traject__transport_modes',
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
            "requester_count": item["requester_count"],
            "pending_count": item["pending_count"],
            "full_dates_count": item["full_dates_count"],
            "available_dates_count": item["available_dates_count"],
        })

    made_page_obj = Paginator(made_reservations, 10).get_page(request.GET.get('made_page', 1))
    received_page_obj = Paginator(received_reservations, 10).get_page(request.GET.get('received_page', 1))

    context = {
        'made_reservations': made_page_obj,
        'received_reservations': received_page_obj,
        'is_abonned': is_abonned,
        'tab': tab,
        'active_count': active_count,
        'history_count': history_count,
    }

    if request.htmx:
        return render(request, 'trajects/reservation/partials/reservations_content.html', context)

    return render(request, 'trajects/reservation/trajets_liste.html', context)
    
@name_required
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

    tab = request.GET.get('tab', 'active')
    if tab not in ('active', 'history'):
        tab = 'active'

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

    today = date.today()
    if tab == 'active':
        rows = [row for row in rows if row['proposal'].date >= today]
    else:
        rows = [row for row in rows if row['proposal'].date < today]

    if rows:
        dates = [row['proposal'].date for row in rows]
        stats = {'first_date': min(dates), 'last_date': max(dates), 'count': len(rows)}
    else:
        stats = {'first_date': None, 'last_date': None, 'count': 0}

    return render(
        request,
        "trajects/reservation/faites_detail.html",
        {
            "header": header,
            "stats": stats,
            "rows": rows,
            "is_abonned": is_abonned,
            "tab": tab,
        },
    )

@name_required
def my_reservations_received_detail(request, proposed_groupe_uid):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = date.today()

    tab = request.GET.get('tab', 'active')
    if tab not in ('active', 'history'):
        tab = 'active'

    proposed_traject = (
        ProposedTraject.objects
        .filter(user=user, groupe_uid=proposed_groupe_uid)
        .select_related('traject')
        .first()
    )
    if not proposed_traject:
        messages.error(request, "Trajet introuvable.")
        return redirect("my_reservations")

    reservations_qs = (
        Reservation.objects.filter(
            proposed_traject__user=user,
            proposed_traject__groupe_uid=proposed_groupe_uid,
        )
        .select_related(
            "user", "user__profile",
            "proposed_traject", "researched_traject",
            "proposed_traject__traject", "researched_traject__traject",
        )
        .prefetch_related(
            "researched_traject__children",
            "researched_traject__children__chld_languages",
            "researched_traject__transport_modes",
        )
    )

    if tab == 'active':
        reservations_qs = reservations_qs.filter(researched_traject__date__gte=today)
    else:
        reservations_qs = reservations_qs.filter(researched_traject__date__lt=today)

    parents_dict = {}
    for r in reservations_qs.order_by('user_id', 'researched_traject__date'):
        uid = r.user_id
        if uid not in parents_dict:
            parents_dict[uid] = {'user': r.user, 'rows': []}
        parents_dict[uid]['rows'].append({
            'reservation': r,
            'proposal': r.proposed_traject,
            'research': r.researched_traject,
            'remaining_places': _available_places(r.proposed_traject),
        })

    parents = list(parents_dict.values())

    all_dates = [row['research'].date for p in parents for row in p['rows']]

    # Heure depuis proposed_traject, fallback sur la première réservation chargée
    first_proposal = next(
        (row['proposal'] for p in parents for row in p['rows']),
        proposed_traject
    )
    stats = {
        'first_date': min(all_dates) if all_dates else None,
        'last_date': max(all_dates) if all_dates else None,
        'count': len(all_dates),
        'departure_time': proposed_traject.departure_time or first_proposal.departure_time,
        'arrival_time': proposed_traject.arrival_time or first_proposal.arrival_time,
    }

    return render(
        request,
        "trajects/reservation/recues_detail.html",
        {
            "proposed_traject": proposed_traject,
            "parents": parents,
            "stats": stats,
            "is_abonned": is_abonned,
            "tab": tab,
        },
    )
