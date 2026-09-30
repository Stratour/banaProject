import re
from itertools import groupby
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.templatetags.static import static as static_url
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .utils.geocoding import get_autocomplete_suggestions, get_place_details
from .utils.display import (
    display_name_and_initials,
    display_name,
    child_labels,
    cancellation_label,
)
from .utils.mail import (
    send_reservation_confirmed_emails,
    send_reservation_rejected_emails,
    send_reservation_canceled_emails,
    send_new_reservation_request_emails,
    send_help_proposed_email,
    send_help_proposed_bulk_email,
    send_member_contact_email,
)
from django.contrib import messages
from accounts.models import Child, FavoriteAddress, Review
from stripe_sub.models import Subscription
from .models import (
    Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation,
    ContactMessage,
)
from .forms import (
    TrajectForm, ProposedTrajectForm, ResearchedTrajectForm,
    SimpleProposedTrajectForm, MemberContactForm,
)
from django.db.models import Q, Min, Max, Count, Avg, Case, When, DateField
from datetime import datetime, timedelta, date
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
import uuid
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.db import transaction
from django.utils.translation import gettext_lazy as _, ngettext

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

# Le nom de la série est ce qui identifie un trajet dans toutes les listes
# (« Mes trajets », « Mes matchings », « Mes réservations »). Sans lui, les
# cartes s'affichaient toutes sous « Mon trajet » / « Ma recherche » et
# devenaient impossibles à distinguer — d'où l'obligation à la création.
GROUPE_NAME_REQUIRED = (
    "Donnez un nom à ce trajet : c'est ce qui vous permet de le reconnaître "
    "dans vos listes (ex : École Charleroi (matin))."
)


class _NotEnoughPlaces(Exception):
    """Sortie de la transaction de confirmation sans écrire (voir manage_reservation)."""


def _available_places(proposal):
    """Places restantes — number_of_places est décrémenté à chaque confirmation."""
    return max(0, proposal.number_of_places)

# Définis dans utils/display.py : les emails en ont besoin et ne peuvent pas
# importer depuis ce module (import circulaire). Alias conservés pour ne pas
# toucher aux call sites existants.
_display_name_and_initials = display_name_and_initials


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

    `dates_count` porte le nom attendu par own_traject_modal.html, la fiche
    de trajet partagée entre les réservations et les matchings.
    """
    _today = today or timezone.now().date()
    return (
        queryset
        .values('groupe_uid')
        .annotate(
            first_date=Min('date'),
            last_date=Max('date'),
            next_date=Min(Case(When(date__gte=_today, then='date'), output_field=DateField())),
            dates_count=Count('id'),
        )
        .order_by('-last_date')
    )


def _distinct_children(researches):
    """Enfants concernés par un groupe de recherches, sans doublon.

    Les occurrences d'un même groupe portent presque toujours les mêmes
    enfants ; on dédoublonne pour ne pas répéter la même pastille.
    """
    seen, children = set(), []
    for research in researches:
        for child in research.children.all():
            if child.id not in seen:
                seen.add(child.id)
                children.append(child)
    return children


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


def _delete_single(request, model, filters, redirect_name, success_msg):
    """Supprime une occurrence unique. POST uniquement."""
    if request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect(redirect_name)
    obj = get_object_or_404(model, user=request.user, **filters)
    obj.delete()
    messages.success(request, success_msg)
    return redirect(redirect_name)


def _parent_reservation_state(user):
    """
    État des réservations portant sur les trajets proposés par `user` (Yaya),
    en une seule requête.

    Retourne (confirmed_ids, pending_ids, canceled_by) où les deux premiers
    sont des ensembles d'ids de ResearchedTraject et le troisième mappe
    l'id du ResearchedTraject vers `Reservation.canceled_by` — la dernière
    annulation en date fait foi si la même date a été réservée puis annulée
    plusieurs fois.
    """
    confirmed_ids, pending_ids, canceled_by = set(), set(), {}

    rows = (
        Reservation.objects
        .filter(proposed_traject__user=user)
        .order_by("reservation_date")
        .values_list("researched_traject_id", "status", "canceled_by")
    )

    for research_id, status, cancel_origin in rows:
        if status == "confirmed":
            confirmed_ids.add(research_id)
        elif status == "pending":
            pending_ids.add(research_id)
        elif status == "canceled":
            canceled_by[research_id] = cancel_origin

    return confirmed_ids, pending_ids, canceled_by


def _match_row_status(research, proposal, today, parent_confirmed_ids, parent_pending_ids, parent_canceled_by=None):
    """
    Statut d'une date de matching côté Yaya, réutilisé à la fois pour
    l'affichage (pastille) et pour savoir si une date est "proposable"
    (cf. propose_help_match). Une réservation n'est jamais créée par le
    Yaya : "confirmed"/"pending" reflètent une réservation déjà initiée
    par le PARENT (via auto_reserve).

    "canceled" est terminal : une date refusée ou annulée n'est plus
    proposable, symétriquement au `is_reservable` du côté parent. Le détail
    de l'annulation (qui, pourquoi) vit dans `parent_canceled_by` et est
    rendu par canceled_badge.html.
    """
    if research.date and research.date < today:
        return "past"
    if research.id in parent_confirmed_ids:
        return "confirmed"
    if research.id in parent_pending_ids:
        return "pending"
    if parent_canceled_by and research.id in parent_canceled_by:
        return "canceled"
    avail = _available_places(proposal) if proposal else 0
    required = len(research.children.all()) or 1
    if avail <= 0:
        return "complet"
    if avail < required:
        return "not_enough"
    return "available"


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
        .prefetch_related("transport_modes", "children", "children__chld_languages")
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
        .prefetch_related("transport_modes", "children", "children__chld_languages")
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
        "page_title": _("Proposer un trajet - Nouveau trajet"),
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

        groupe_name = (request.POST.get("groupe_name") or "").strip()
        groupe_uid = uuid.uuid4()

        if not groupe_name:
            messages.error(request, _(GROUPE_NAME_REQUIRED))
            proposed_trajects, success = [], False
        else:
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
            groupe_name = (request.POST.get("groupe_name") or "").strip()
            groupe_uid = uuid.uuid4()

            if not groupe_name:
                messages.error(request, _(GROUPE_NAME_REQUIRED))
                proposed_trajects, success = [], False
            else:
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
            "page_title": _("Rechercher un trajet rayon - Nouveau trajet"),
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
        "page_title": _("Rechercher un trajet - Nouveau trajet"),
        "days_of_week": [
            ("1", _("Lundi")), ("2", _("Mardi")), ("3", _("Mercredi")),
            ("4", _("Jeudi")), ("5", _("Vendredi")), ("6", _("Samedi")), ("7", _("Dimanche")),
        ],
        "service": service,
    }

    if request.method == "POST":
        traject_form = TrajectForm(request.POST)
        researched_form = ResearchedTrajectForm(request.POST, user=request.user)

        groupe_name = (request.POST.get("groupe_name") or "").strip()
        groupe_uid = uuid.uuid4()

        if not groupe_name:
            messages.error(request, _(GROUPE_NAME_REQUIRED))
            researched_trajects, success = [], False
        else:
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

        messages.warning(request, _("Veuillez corriger les erreurs dans le formulaire."))

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

def _resolve_recurrent_dates(request, recurrence_type, date_debut, date_fin, selected_days):
    """
    Calcule la liste finale des dates à créer, en tenant compte :
    - de la sélection libre du calendrier (mode "one_week" / occasionnel),
      transmise via le champ caché POST "selected_dates" (CSV de dates ISO) ;
      si présente, elle prime sur le calcul jour(s)-de-semaine + plage ;
    - des dates explicitement exclues par l'utilisateur (POST "excluded_dates",
      CSV de dates ISO), applicable à tous les modes de récurrence ;
    - des dates déjà passées, silencieusement ignorées (l'utilisateur n'a pas
      à revenir corriger son formulaire : on ne crée que les dates à venir).
    """
    selected_raw = (request.POST.get("selected_dates") or "").strip()
    excluded_raw = (request.POST.get("excluded_dates") or "").strip()
    excluded_set = {d for d in excluded_raw.split(",") if d}

    if recurrence_type == "one_week" and selected_raw:
        recurrent_dates = sorted({
            datetime.strptime(d, "%Y-%m-%d").date()
            for d in selected_raw.split(",") if d
        })
    else:
        recurrent_dates = generate_recurrent_dates(
            date_debut=date_debut,
            date_fin=date_fin,
            recurrence_type=recurrence_type,
            specific_days=selected_days,
        )

    if excluded_set:
        recurrent_dates = [d for d in recurrent_dates if d.isoformat() not in excluded_set]

    today = date.today()
    upcoming_dates = [d for d in recurrent_dates if d >= today]

    skipped_count = len(recurrent_dates) - len(upcoming_dates)

    if skipped_count and not upcoming_dates:
        messages.error(
            request,
            _("Toutes les dates choisies sont déjà passées : aucun trajet n’a été créé.")
        )
    elif skipped_count:
        messages.info(
            request,
            ngettext(
                "%(count)s date déjà passée a été ignorée.",
                "%(count)s dates déjà passées ont été ignorées.",
                skipped_count,
            ) % {"count": skipped_count}
        )

    return upcoming_dates


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

    recurrent_dates = _resolve_recurrent_dates(
        request=request,
        recurrence_type=recurrence_type,
        date_debut=date_debut,
        date_fin=date_fin,
        selected_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    # Les dates passées ayant pu être écartées, on recale la métadonnée de
    # récurrence sur la première occurrence réellement créée.
    date_debut = recurrent_dates[0]

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

    recurrent_dates = _resolve_recurrent_dates(
        request=request,
        recurrence_type=recurrence_type,
        date_debut=date_debut,
        date_fin=date_fin,
        selected_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    # Les dates passées ayant pu être écartées, on recale la métadonnée de
    # récurrence sur la première occurrence réellement créée.
    date_debut = recurrent_dates[0]

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

    recurrent_dates = _resolve_recurrent_dates(
        request=request,
        recurrence_type=recurrence_type,
        date_debut=date_debut,
        date_fin=date_fin,
        selected_days=selected_days,
    )

    if not recurrent_dates:
        return None, False

    # Les dates passées ayant pu être écartées, on recale la métadonnée de
    # récurrence sur la première occurrence réellement créée.
    date_debut = recurrent_dates[0]

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
        occurrences = list(
            ProposedTraject.objects
            .filter(user=user, groupe_uid=g["groupe_uid"], is_active=True)
            .order_by("date", "departure_time")
        )
        if not occurrences:
            continue
        header = occurrences[0]
        header.groupe_count = g["dates_count"]
        header.groupe_first_date = g["first_date"]
        header.groupe_last_date = g["last_date"]
        header.occurrences = occurrences  # chaque occurrence expose déjà .is_past (property du modèle)
        proposed_headers.append(header)

    return render(request, "trajects/proposition/trajets_liste.html", {
        "proposed_trajects": proposed_headers,
        "is_abonned": is_abonned,
        "page_title": _("Proposer un trajet - Mes trajets"),
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
        occurrences = list(
            ProposedTraject.objects
            .filter(user=user, is_simple=True, is_active=True, groupe_uid=g['groupe_uid'])
            .order_by('date', 'departure_time')
        )
        if not occurrences:
            continue

        header = occurrences[0]
        header.groupe_count = g['dates_count']
        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        header.occurrences = occurrences  # chaque occurrence expose déjà .is_past (property du modèle)
        headers.append(header)

    return render(request, 'trajects/proposition_rayon/trajets_liste.html', {
        'simple_trajects': headers,
        'is_abonned': is_abonned,
        'page_title': _("Rechercher un trajet rayon - Mes trajets"),
    })
    
@name_required
def my_researched_trajects(request):
    user = request.user
    is_abonned = Subscription.is_user_abonned(user)
    today = timezone.now().date()

    groupes = _aggregate_groupes(
        ResearchedTraject.objects.filter(user=user, is_active=True)
    )

    researched_headers = []
    for g in groupes:
        occurrences = list(
            ResearchedTraject.objects
            .filter(user=user, groupe_uid=g['groupe_uid'], is_active=True)
            .order_by('date', 'departure_time')
        )
        if not occurrences:
            continue

        # ResearchedTraject n'a pas de property is_past (contrairement à
        # ProposedTraject) — on la calcule ici pour le template.
        for occ in occurrences:
            occ.is_past = bool(occ.date and occ.date < today)

        header = occurrences[0]
        # ✅ On “colle” des infos de groupe sur l’objet pour le template
        header.groupe_count = g['dates_count']
        header.groupe_first_date = g['first_date']
        header.groupe_last_date = g['last_date']
        header.occurrences = occurrences

        researched_headers.append(header)


    return render(request, 'trajects/recherche/trajets_liste.html', {
        'researched_trajects': researched_headers,
        'is_abonned': is_abonned,
        'page_title': _("Rechercher un trajet - Mes trajets"),
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
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

    # "confirmed"/"pending"/"canceled" reflètent des réservations déjà initiées
    # par le PARENT (auto_reserve) — le Yaya ne crée jamais de Reservation
    # lui-même, voir _match_row_status.
    parent_confirmed_ids, parent_pending_ids, parent_canceled_by = _parent_reservation_state(user)

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

        proposed_qs = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=False, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
        )
        matched_researches = _collect_matches(proposed_qs)
        proposed_by_date = {p.date: p for p in proposed_qs}

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            pair_map.setdefault(key, []).append(research)

        if not pair_map:
            continue

        matches = []
        for (researched_groupe_uid, parent_user_id), researches in pair_map.items():
            researches_sorted = sorted(
                researches,
                key=lambda r: (r.date or today, r.departure_time or datetime.min.time()),
            )
            representative = researches_sorted[0]
            rows = _build_match_rows(
                researches_sorted, proposed_by_date, today,
                extra_fields_fn=lambda research, proposal: {
                    "status": _match_row_status(
                        research, proposal, today,
                        parent_confirmed_ids, parent_pending_ids, parent_canceled_by,
                    ),
                    "canceled_by": parent_canceled_by.get(research.id),
                },
            )
            ratings = Review.objects.filter(reviewed_user=representative.user).aggregate(
                avg=Avg("rating"), count=Count("id")
            )
            matches.append({
                "user": representative.user,
                "groupe_uid": researched_groupe_uid,
                # Unique par carte de la page : un même groupe de recherche peut
                # correspondre à plusieurs de mes trajets, et les <dialog> des
                # pastilles enfant se disputeraient alors le même id HTML.
                "scope": f"{g['groupe_uid']}-{researched_groupe_uid}",
                "children": _distinct_children(researches_sorted),
                "traject": representative.traject,
                "departure_time": representative.departure_time,
                "arrival_time": representative.arrival_time,
                "matched_date_debut": researches_sorted[0].date,
                "matched_date_fin": researches_sorted[-1].date,
                "dates_count": len(rows),
                "rows": rows,
                "languages": representative.user.profile.languages.all(),
                "average_rating": round(ratings["avg"] or 0, 1),
                "reviews_count": ratings["count"] or 0,
                "has_available": any(row["status"] == "available" for row in rows),
            })

        headers.append({
            "header": header,
            "stats": g,
            "matches": matches,
            "matches_count": len(matches),
        })

    return render(request, "trajects/proposition/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
        "today": today,
        "page_title": _("Proposer un trajet - Mes matchings"),
    })

@name_required
def my_matchings_simple(request):
    """
    Yaya simple rayon -> match avec parent researched.
    """
    user = request.user
    today = timezone.now().date()
    is_abonned = Subscription.is_user_abonned(user)
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

    parent_confirmed_ids, parent_pending_ids, parent_canceled_by = _parent_reservation_state(user)

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
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
            .order_by("date", "departure_time")
            .first()
        )
        if not header:
            continue

        proposed_qs = (
            ProposedTraject.objects
            .filter(user=user, is_active=True, is_simple=True, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject", "user", "user__profile")
            .prefetch_related("transport_modes", "languages")
        )
        matched_researches = _collect_matches(proposed_qs)
        proposed_by_date = {p.date: p for p in proposed_qs}

        pair_map = {}
        for research in matched_researches:
            key = (research.groupe_uid, research.user_id)
            pair_map.setdefault(key, []).append(research)

        if not pair_map:
            continue

        matches = []
        for (researched_groupe_uid, parent_user_id), researches in pair_map.items():
            researches_sorted = sorted(
                researches,
                key=lambda r: (r.date or today, r.departure_time or datetime.min.time()),
            )
            representative = researches_sorted[0]
            rows = _build_match_rows(
                researches_sorted, proposed_by_date, today,
                extra_fields_fn=lambda research, proposal: {
                    "status": _match_row_status(
                        research, proposal, today,
                        parent_confirmed_ids, parent_pending_ids, parent_canceled_by,
                    ),
                    "canceled_by": parent_canceled_by.get(research.id),
                },
            )
            ratings = Review.objects.filter(reviewed_user=representative.user).aggregate(
                avg=Avg("rating"), count=Count("id")
            )
            matches.append({
                "user": representative.user,
                "groupe_uid": researched_groupe_uid,
                # Unique par carte de la page : un même groupe de recherche peut
                # correspondre à plusieurs de mes trajets, et les <dialog> des
                # pastilles enfant se disputeraient alors le même id HTML.
                "scope": f"{g['groupe_uid']}-{researched_groupe_uid}",
                "children": _distinct_children(researches_sorted),
                "traject": representative.traject,
                "departure_time": representative.departure_time,
                "arrival_time": representative.arrival_time,
                "matched_date_debut": researches_sorted[0].date,
                "matched_date_fin": researches_sorted[-1].date,
                "dates_count": len(rows),
                "rows": rows,
                "languages": representative.user.profile.languages.all(),
                "average_rating": round(ratings["avg"] or 0, 1),
                "reviews_count": ratings["count"] or 0,
                "has_available": any(row["status"] == "available" for row in rows),
            })

        headers.append({
            "header": header,
            "stats": g,
            "matches": matches,
            "matches_count": len(matches),
        })

    return render(request, "trajects/proposition_rayon/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
        "today": today,
        "page_title": _("Rechercher un trajet rayon - Mes matchings"),
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
    profile = user.profile
    is_subscription_complete = is_abonned and bool(
        profile.ci_is_verified and profile.document_bvm and profile.profile_picture
    )

    # Réservations déjà faites par le parent connecté, réutilisées pour
    # savoir quel bouton afficher par date dans l'accordéon (cf. reservation_key
    # dans _build_match_rows ci-dessous).
    my_pending_keys = set(
        f"{proposal_id}_{research_id}"
        for proposal_id, research_id in Reservation.objects.filter(user=user, status="pending")
        .values_list("proposed_traject_id", "researched_traject_id")
    )
    my_confirmed_keys = set(
        f"{proposal_id}_{research_id}"
        for proposal_id, research_id in Reservation.objects.filter(user=user, status="confirmed")
        .values_list("proposed_traject_id", "researched_traject_id")
    )
    # Pour une annulation, on garde aussi l'origine (`canceled_by`) : le parent
    # doit pouvoir distinguer « annulée par vous » d'un refus du conducteur ou
    # d'une annulation automatique (cf. canceled_badge.html). La dernière
    # annulation en date fait foi.
    my_canceled_by = {
        f"{proposal_id}_{research_id}": canceled_by
        for proposal_id, research_id, canceled_by in Reservation.objects
        .filter(user=user, status="canceled")
        .order_by("reservation_date")
        .values_list("proposed_traject_id", "researched_traject_id", "canceled_by")
    }
    my_canceled_keys = set(my_canceled_by)

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

        researched_qs = (
            ResearchedTraject.objects
            .filter(user=user, is_active=True, groupe_uid=g["groupe_uid"], date__gte=today)
            .select_related("traject")
            .prefetch_related("transport_modes", "children")
        )
        matched_proposals = _collect_matches(researched_qs)

        pair_map = {}
        for proposal in matched_proposals:
            key = (proposal.groupe_uid, proposal.user_id)
            pair_map.setdefault(key, []).append(proposal)

        if not pair_map:
            continue

        matches = []
        for (proposed_groupe_uid, matched_user_id), proposals in pair_map.items():
            proposals_sorted = sorted(
                proposals,
                key=lambda p: (p.date or today, p.departure_time or datetime.min.time()),
            )
            representative = proposals_sorted[0]
            proposed_by_date = {p.date: p for p in proposals_sorted}
            rows = _build_match_rows(
                researched_qs, proposed_by_date, today,
                skip_if_no_proposal=True,
                extra_fields_fn=lambda research, proposal: {
                    "proposal": proposal,
                    "reservation_key": f"{proposal.id}_{research.id}",
                    "canceled_by": my_canceled_by.get(f"{proposal.id}_{research.id}"),
                    "is_simple": proposal.is_simple,
                    "radius_km": proposal.search_radius_km if proposal.is_simple else None,
                    "is_reservable": (
                        not (research.date and research.date < today)
                        and f"{proposal.id}_{research.id}" not in my_confirmed_keys
                        and f"{proposal.id}_{research.id}" not in my_pending_keys
                        and f"{proposal.id}_{research.id}" not in my_canceled_keys
                    ),
                },
            )
            ratings = Review.objects.filter(reviewed_user=representative.user).aggregate(
                avg=Avg("rating"), count=Count("id")
            )
            matches.append({
                "user": representative.user,
                "groupe_uid": proposed_groupe_uid,
                "traject": representative.traject,
                "departure_time": representative.departure_time,
                "arrival_time": representative.arrival_time,
                "search_radius_km": representative.search_radius_km,
                "matched_date_debut": proposals_sorted[0].date,
                "matched_date_fin": proposals_sorted[-1].date,
                "dates_count": len(rows),
                "rows": rows,
                "reservable_count": sum(1 for r in rows if r["is_reservable"]),
                "languages": representative.user.profile.languages.all(),
                "average_rating": round(ratings["avg"] or 0, 1),
                "reviews_count": ratings["count"] or 0,
            })

        headers.append({
            "header": header,
            "stats": g,
            "matches": matches,
            "matches_count": len(matches),
        })

    return render(request, "trajects/recherche/matchings.html", {
        "groups": headers,
        "is_abonned": is_abonned,
        "is_subscription_complete": is_subscription_complete,
        "my_pending_keys": my_pending_keys,
        "my_confirmed_keys": my_confirmed_keys,
        "my_canceled_keys": my_canceled_keys,
        "today": today,
        "page_title": _("Rechercher un trajet - Mes matchings"),
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
        redirect_name="my_proposed_trajects",
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
        redirect_name="my_simple_trajects",
        success_msg="La date du trajet simplifié a été supprimée.",
    )

@login_required
def delete_researched_traject(request, groupe_uid, pk):
    return _delete_single(
        request, ResearchedTraject,
        filters={"pk": pk, "groupe_uid": groupe_uid},
        redirect_name="my_researched_trajects",
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
            messages.success(request, 'Trajet mis à jour avec succès.')
            return redirect('profile')
        else:
            messages.warning(request, 'Veuillez corriger les erreurs dans le formulaire.')
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


def _accept_reservation(reservation):
    """Confirme une demande et annule celles que le parent a faites ailleurs
    pour la même date. Lève _NotEnoughPlaces sans rien écrire s'il ne reste
    pas assez de places. Renvoie la liste des demandes annulées en cascade.

    Partagé par manage_reservation (unitaire) et manage_reservations_bulk.
    """
    requested_places = int(reservation.number_of_places or 0)
    superseded = []

    # Le décompte des places est un lire-puis-écrire : sans verrou, deux
    # confirmations concurrentes sur le même trajet liraient le même stock
    # et le sur-vendraient. On relit la ligne sous select_for_update.
    with transaction.atomic():
        proposal = (
            ProposedTraject.objects
            .select_for_update()
            .get(pk=reservation.proposed_traject_id)
        )

        # IMPORTANT :
        # _available_places() doit être la seule source de vérité pour savoir
        # combien de places sont encore disponibles sur le trajet proposé.
        remaining_places = _available_places(proposal)

        if requested_places > remaining_places:
            raise _NotEnoughPlaces

        reservation.status = "confirmed"
        reservation.canceled_by = None
        reservation.save(update_fields=["status", "canceled_by"])

        proposal.confirmed_users.add(reservation.user)

        # number_of_places représente les places DISPONIBLES : on décrémente.
        proposal.number_of_places = remaining_places - requested_places
        proposal.save(update_fields=["number_of_places"])

        # Le parent a pu solliciter plusieurs personnes pour cette même date :
        # sans cette cascade, chacune pourrait confirmer de son côté et
        # l'enfant se retrouverait accompagné deux fois.
        if reservation.researched_traject_id:
            superseded = list(
                Reservation.objects
                .filter(
                    user=reservation.user,
                    researched_traject_id=reservation.researched_traject_id,
                    status="pending",
                )
                .exclude(pk=reservation.pk)
                .select_related(
                    "proposed_traject", "proposed_traject__user",
                    "proposed_traject__traject",
                )
            )
            for other in superseded:
                other.status = "canceled"
                other.canceled_by = "auto"
                other.save(update_fields=["status", "canceled_by"])

    return superseded


def _research_already_confirmed(user, researched_traject):
    """Cette date de recherche est-elle déjà couverte par un accompagnateur confirmé ?"""
    return Reservation.objects.filter(
        user=user,
        researched_traject=researched_traject,
        status="confirmed",
    ).exists()


def _reservation_action_response(request, open_key, next_url):
    """Réponse commune aux actions sur une réservation.

    En HTMX on renvoie le partial complet re-calculé (la liste, les compteurs et
    le calendrier changent tous en même temps) ; `open_key` garde le volet
    concerné déplié. Sans HTMX, redirection classique — les formulaires restent
    donc fonctionnels sans JavaScript.
    """
    if request.htmx:
        return render(request, RESERVATIONS_PARTIAL, _reservations_context(request, open_key))
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or "my_reservations")


# Quotas du formulaire de contact, comptés en base : le cache du projet est un
# LocMemCache propre à chaque worker, il compterait donc autant de fois qu'il y
# a de process gunicorn.
CONTACT_MAX_PER_HOUR = 10
CONTACT_MAX_PER_RECIPIENT_PER_HOUR = 3
CONTACT_FORM_PARTIAL = "trajects/reservation/partials/contact_form.html"


def _contact_form_for(open_key, data=None):
    """Formulaire de contact d'une carte.

    L'auto_id est préfixé par la clé de la carte : la page affiche autant de
    formulaires que de personnes, sans ça tous les <textarea> partageraient le
    même id et les <label> pointeraient tous vers le premier.
    """
    return MemberContactForm(data, auto_id=f"id-{slugify(open_key)}-%s")


def _can_contact(sender, recipient):
    """Même règle que l'affichage du bouton : au moins une réservation confirmée
    entre les deux, dans un sens ou dans l'autre. Avant ça, il n'y a rien à
    convenir — et aucune raison d'ouvrir un canal d'écriture."""
    if sender == recipient:
        return False
    return Reservation.objects.filter(status="confirmed").filter(
        Q(user=sender, proposed_traject__user=recipient)
        | Q(user=recipient, proposed_traject__user=sender)
    ).exists()


def _contact_sender_name(user):
    """Nom affiché comme expéditeur du message.

    Jamais l'adresse email en repli : elle n'apparaîtrait alors dans l'objet du
    mail, alors qu'elle ne doit se découvrir qu'au moment de répondre.
    """
    return display_name(user, fallback="Un membre")


def _contact_quota_error(sender, recipient):
    """Libellé de l'erreur si un quota horaire est dépassé, None sinon."""
    cutoff = timezone.now() - timedelta(hours=1)
    recent = ContactMessage.objects.filter(sender=sender, created_at__gte=cutoff)
    if recent.count() >= CONTACT_MAX_PER_HOUR:
        return "Vous avez envoyé trop de messages dans la dernière heure. Réessayez plus tard."
    if recent.filter(recipient=recipient).count() >= CONTACT_MAX_PER_RECIPIENT_PER_HOUR:
        return (
            "Vous avez déjà écrit plusieurs fois à cette personne dans la dernière "
            "heure. Laissez-lui le temps de vous répondre."
        )
    return None


def _contact_response(request, recipient, form, open_key, label, next_url, sent=False):
    """Réponse du formulaire de contact.

    On ne re-rend que le corps de la modale, pas toute la liste : aucune donnée
    de réservation ne change, et un re-rendu global ferait perdre le message
    saisi en cas d'erreur de validation. Sans HTMX, redirection classique — le
    formulaire reste utilisable sans JavaScript.
    """
    if request.htmx:
        return render(request, CONTACT_FORM_PARTIAL, {
            "contact_form": form,
            "contact_open_key": open_key,
            "contact_recipient_id": recipient.id,
            "contact_recipient_name": _display_name_and_initials(recipient)[0],
            "contact_label": label,
            "contact_sent": sent,
            # Les toasts sont rendus hors du fragment swappé : sans ce drapeau,
            # le message n'apparaîtrait qu'au chargement suivant. Il n'est posé
            # que par cette vue — person_card.html inclut le même partial pour
            # le rendu initial et dupliquerait sinon #toast-host à chaque carte.
            "contact_toast": True,
        })
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    return redirect(next_url or "my_reservations")


@login_required
@require_http_methods(["POST"])
def contact_member(request, user_id):
    """Message libre à l'autre partie d'une réservation confirmée.

    Remplace l'ancien lien mailto: : celui-ci dépendait du client mail déclaré
    dans le navigateur et n'ouvrait rien chez une partie des membres (Brave,
    Firefox sans handler, mobile sans compte configuré), les bloquant au moment
    précis où ils devaient convenir de l'heure et du point de rendez-vous.
    """
    recipient = get_object_or_404(User.objects.select_related("profile"), id=user_id)
    next_url = request.POST.get("next")
    open_key = request.POST.get("open_key") or f"contact-{recipient.id}"
    # Libellé purement indicatif : tronqué et mis sur une ligne, il ne sert que
    # de contexte dans le corps du mail — jamais dans le sujet, où il ouvrirait
    # une injection d'en-tête.
    label = " ".join(request.POST.get("context_label", "").split())[:120]

    form = _contact_form_for(open_key, request.POST)

    def refuse(message):
        messages.error(request, message)
        return _contact_response(request, recipient, form, open_key, label, next_url)

    # Le bouton n'est affiché qu'aux abonnés : la condition est rejouée ici, où
    # elle est opposable. `subscription_complete_required` serait plus strict
    # que l'affichage (il exige CI + BVM + photo) et rendrait le bouton mort
    # pour une partie des abonnés.
    if not Subscription.is_user_abonned(request.user):
        return refuse("Vous devez être abonné pour contacter un membre.")

    if not _can_contact(request.user, recipient):
        return refuse("Vous ne pouvez contacter cette personne qu'après une réservation confirmée.")

    if not form.is_valid():
        return _contact_response(request, recipient, form, open_key, label, next_url)

    quota_error = _contact_quota_error(request.user, recipient)
    if quota_error:
        return refuse(quota_error)

    contact_message = ContactMessage.objects.create(
        sender=request.user,
        recipient=recipient,
        context_label=label,
        body=form.cleaned_data["body"],
    )

    # Le message reste en base même si le SMTP tombe : on ne le perd pas, et le
    # quota reste juste.
    if send_member_contact_email(contact_message, _contact_sender_name(request.user)):
        contact_message.email_sent = True
        contact_message.save(update_fields=["email_sent"])
        messages.success(
            request,
            f"Message envoyé à {_display_name_and_initials(recipient)[0]}.",
        )
        return _contact_response(request, recipient, None, open_key, label, next_url, sent=True)

    return refuse("L'envoi a échoué. Réessayez dans quelques instants.")


@subscription_complete_required
@require_http_methods(["POST"])
def manage_reservation(request, reservation_id, action):
    """Confirmation / refus d'une demande, côté propriétaire du trajet proposé."""
    next_url = request.POST.get("next")
    open_key = request.POST.get("open_key")
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "user",
            "user__profile",
            "proposed_traject",
            "proposed_traject__user",
            "proposed_traject__traject",
            "researched_traject",
        ),
        id=reservation_id,
        proposed_traject__user=request.user,
    )

    # Sécurité : on n'accepte que deux actions possibles
    if action not in ["accept", "reject"]:
        messages.error(request, "Action invalide.")
        return _reservation_action_response(request, open_key, next_url)

    # =========================
    # ACCEPTATION
    # =========================
    if action == "accept":
        # Évite de reconfirmer une réservation déjà confirmée
        if reservation.status == "confirmed":
            messages.warning(request, "Cette réservation est déjà confirmée.")
            return _reservation_action_response(request, open_key, next_url)

        # Évite de confirmer une réservation déjà annulée
        if reservation.status == "canceled":
            messages.warning(request, "Cette réservation a déjà été annulée.")
            return _reservation_action_response(request, open_key, next_url)

        # Nombre de places demandées par cette réservation
        requested_places = int(reservation.number_of_places or 0)

        if requested_places <= 0:
            messages.error(request, "Le nombre de places demandé est invalide.")
            return _reservation_action_response(request, open_key, next_url)

        try:
            superseded = _accept_reservation(reservation)
        except _NotEnoughPlaces:
            messages.error(
                request,
                "Pas assez de places restantes pour confirmer cette réservation.",
            )
            return _reservation_action_response(request, open_key, next_url)

        # Emails après commit. Les demandes supplantées peuvent concerner
        # plusieurs yayas : l'envoi groupé les regroupe par destinataire.
        send_reservation_confirmed_emails([reservation])
        send_reservation_canceled_emails(superseded)

        if superseded:
            messages.success(
                request,
                f"Réservation confirmée. {len(superseded)} autre(s) demande(s) du parent "
                "pour cette date ont été annulées automatiquement.",
            )
        else:
            messages.success(request, "Réservation confirmée.")
        return _reservation_action_response(request, open_key, next_url)

    # =========================
    # REFUS
    # =========================
    # Si déjà annulée, inutile de refaire l'action
    if reservation.status == "canceled":
        messages.warning(request, "Cette réservation est déjà annulée.")
        return _reservation_action_response(request, open_key, next_url)

    # Si déjà confirmée, on évite de la refuser ici sans logique métier claire
    # car sinon il faudrait potentiellement remettre les places disponibles
    if reservation.status == "confirmed":
        messages.warning(request, "Cette réservation est déjà confirmée.")
        return _reservation_action_response(request, open_key, next_url)

    reservation.status = "canceled"
    reservation.canceled_by = "yaya"
    reservation.save(update_fields=["status", "canceled_by"])

    send_reservation_rejected_emails([reservation])

    messages.success(request, "Réservation refusée.")
    return _reservation_action_response(request, open_key, next_url)


@subscription_complete_required
@require_http_methods(["POST"])
def manage_reservations_bulk(request):
    """Confirme ou refuse plusieurs dates cochées en une fois.

    Miroir de auto_reserve_bulk côté parent : le yaya coche les dates d'un
    demandeur (ou clique « Tout sélectionner ») et répond d'un coup, au lieu
    d'un aller-retour par date.

    Chaque acceptation est atomique de son côté : si les places viennent à
    manquer en cours de lot, les dates déjà confirmées le restent et les
    autres sont simplement comptées comme non traitées.
    """
    next_url = request.POST.get("next")
    open_key = request.POST.get("open_key")
    action = request.POST.get("action")

    if action not in ("accept", "reject"):
        messages.error(request, "Action invalide.")
        return _reservation_action_response(request, open_key, next_url)

    ids = [i for i in request.POST.getlist("reservation_ids") if i.isdigit()]
    if not ids:
        messages.warning(request, "Veuillez sélectionner au moins une date.")
        return _reservation_action_response(request, open_key, next_url)

    reservations = list(
        Reservation.objects
        .filter(
            id__in=ids,
            proposed_traject__user=request.user,
            status="pending",
        )
        .select_related(
            "user", "proposed_traject", "proposed_traject__user",
            "proposed_traject__traject", "researched_traject",
        )
        .order_by("researched_traject__date")
    )

    if not reservations:
        messages.warning(request, "Aucune demande en attente dans votre sélection.")
        return _reservation_action_response(request, open_key, next_url)

    done = 0
    skipped = 0
    to_notify = []
    superseded_all = []

    for reservation in reservations:
        if action == "accept":
            try:
                superseded_all.extend(_accept_reservation(reservation))
            except _NotEnoughPlaces:
                skipped += 1
                continue
            to_notify.append(reservation)
            done += 1
        else:
            reservation.status = "canceled"
            reservation.canceled_by = "yaya"
            reservation.save(update_fields=["status", "canceled_by"])
            to_notify.append(reservation)
            done += 1

    # Emails après écriture, jamais dans la transaction. Un seul message par
    # parent pour tout le lot : répondre à dix dates d'un clic ne doit pas
    # remplir sa boîte de dix messages identiques à une date près.
    if action == "accept":
        send_reservation_confirmed_emails(to_notify)
    else:
        send_reservation_rejected_emails(to_notify)
    send_reservation_canceled_emails(superseded_all)

    verb = "confirmée" if action == "accept" else "refusée"
    parts = [f"{done} date(s) {verb}(s)."]
    if skipped:
        parts.append(f"{skipped} non confirmée(s), faute de places restantes.")
    if superseded_all:
        parts.append(
            f"{len(superseded_all)} demande(s) du parent ailleurs pour ces dates "
            "ont été annulées automatiquement."
        )
    if done:
        messages.success(request, " ".join(parts))
    else:
        messages.error(request, " ".join(parts))

    return _reservation_action_response(request, open_key, next_url)


@name_required
@require_http_methods(["POST"])
def cancel_reservation(request, reservation_id):
    """Annulation par le PARENT de sa propre demande.

    Limitée aux demandes encore "pending" : les places ne sont décrémentées
    qu'à la confirmation (voir manage_reservation), il n'y a donc rien à
    restituer. Une réservation déjà confirmée doit se régler avec le yaya.
    """
    next_url = request.POST.get("next")
    open_key = request.POST.get("open_key")
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "proposed_traject",
            "proposed_traject__user",
            "proposed_traject__traject",
        ),
        id=reservation_id,
        user=request.user,
    )

    if reservation.status == "canceled":
        messages.warning(request, "Cette demande est déjà annulée.")
        return _reservation_action_response(request, open_key, next_url)

    if reservation.status != "pending":
        messages.error(
            request,
            "Cette demande est déjà confirmée : contactez le conducteur pour l'annuler.",
        )
        return _reservation_action_response(request, open_key, next_url)

    reservation.status = "canceled"
    reservation.canceled_by = "parent"
    reservation.save(update_fields=["status", "canceled_by"])

    send_reservation_canceled_emails([reservation])

    messages.success(request, "Votre demande de réservation a été annulée.")
    return _reservation_action_response(request, open_key, next_url)

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

    # Une date déjà confirmée auprès de quelqu'un d'autre : solliciter un
    # second accompagnateur recréerait la double réservation que la cascade
    # de manage_reservation vient justement d'éviter.
    if _research_already_confirmed(request.user, researched_traject):
        messages.warning(
            request,
            "Cette date est déjà confirmée avec un autre accompagnateur.",
        )
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

    send_new_reservation_request_emails([reservation])

    messages.success(request, "Votre demande de réservation a été envoyée.")
    return redirect(next_url or 'my_matchings_researched')

@subscription_complete_required
@transaction.atomic
def auto_reserve_bulk(request):
    """
    Version groupée de auto_reserve : le parent coche plusieurs dates dans
    un même panneau de matching (une par ligne, valeur "proposedId_researchId")
    et envoie une seule requête au lieu de cliquer "Réserver" pour chacune.
    """
    next_url = request.POST.get("next")

    if request.method != "POST":
        return redirect(next_url or 'my_matchings_researched')

    pairs = request.POST.getlist("pairs")
    if not pairs:
        messages.warning(request, "Veuillez sélectionner au moins une date.")
        return redirect(next_url or 'my_matchings_researched')

    created_reservations = []
    skipped_count = 0

    for pair in pairs:
        proposed_id_str, _, researched_id_str = pair.partition("_")
        if not proposed_id_str.isdigit() or not researched_id_str.isdigit():
            skipped_count += 1
            continue

        proposed_traject = ProposedTraject.objects.filter(id=int(proposed_id_str), is_active=True).first()
        researched_traject = ResearchedTraject.objects.filter(
            id=int(researched_id_str), user=request.user, is_active=True
        ).first()

        if not proposed_traject or not researched_traject or proposed_traject.user == request.user:
            skipped_count += 1
            continue

        existing = Reservation.objects.filter(
            user=request.user,
            proposed_traject=proposed_traject,
            researched_traject=researched_traject
        ).exclude(status="canceled").exists()

        if existing or _research_already_confirmed(request.user, researched_traject):
            skipped_count += 1
            continue

        requested_places = researched_traject.children.count()
        reservation = Reservation.objects.create(
            user=request.user,
            proposed_traject=proposed_traject,
            researched_traject=researched_traject,
            number_of_places=requested_places,
            status='pending'
        )
        reservation.transport_modes.set(researched_traject.transport_modes.all())
        created_reservations.append(reservation)

    # Un seul email au yaya pour tout le lot : une sélection de dix dates lui
    # envoyait dix messages identiques à une date près.
    # send_new_reservation_request_emails regroupe par destinataire, et
    # on_commit évite de prévenir pour des réservations qu'un rollback de
    # cette vue atomique effacerait.
    created_count = len(created_reservations)
    if created_reservations:
        transaction.on_commit(
            lambda: send_new_reservation_request_emails(created_reservations)
        )

    if created_count:
        messages.success(
            request,
            f"{created_count} demande(s) de réservation envoyée(s)." if created_count > 1
            else "Votre demande de réservation a été envoyée."
        )
    if skipped_count:
        messages.warning(request, f"{skipped_count} date(s) ignorée(s) (déjà réservée(s) ou indisponible(s)).")

    return redirect(next_url or 'my_matchings_researched')

@subscription_complete_required
def propose_help(request, researched_id):
    research = get_object_or_404(ResearchedTraject, id=researched_id)
    next_url = request.POST.get("next")

    session_key = f"help_notified_{request.user.id}_{researched_id}"
    if request.session.get(session_key, False):
        messages.warning(request, "Vous avez déjà signalé votre disponibilité pour ce trajet.")
        return redirect(next_url or 'my_matchings_proposed')
    request.session[session_key] = True

    send_help_proposed_email(research, request.user)

    messages.success(request, "Votre aide a été proposée et le parent a été informé par email.")
    return redirect(next_url or 'my_matchings_proposed')

@subscription_complete_required
def propose_help_match(request, proposed_groupe_uid, researched_groupe_uid, parent_user_id):
    """
    Signale en un clic, au parent d'un matching, que le Yaya a des dates
    disponibles — un seul email groupé (pas un par date). Remplace, côté
    matchings.html, les anciens clics répétés sur propose_help par date.
    Utilisé aussi bien pour les trajets précis (proposition) que pour les
    trajets dans un rayon (proposition_rayon) — le groupe_uid identifie
    déjà les deux sans ambiguïté.
    """
    user = request.user
    today = timezone.now().date()
    next_url = request.POST.get("next")

    proposed_qs = (
        ProposedTraject.objects
        .filter(user=user, is_active=True, groupe_uid=proposed_groupe_uid, date__gte=today)
        .select_related("traject")
    )
    header = proposed_qs.first()
    fallback_url = 'my_matchings_simple' if header and header.is_simple else 'my_matchings_proposed'
    if not header:
        messages.error(request, "Groupe introuvable.")
        return redirect(next_url or fallback_url)

    proposed_by_date = {p.date: p for p in proposed_qs}

    matched_researches = [
        r for r in _collect_matches(proposed_qs)
        if r.groupe_uid == researched_groupe_uid and r.user_id == parent_user_id
    ]
    if not matched_researches:
        messages.error(request, "Aucune date correspondante trouvée pour ce matching.")
        return redirect(next_url or fallback_url)

    parent_confirmed_ids, parent_pending_ids, parent_canceled_by = _parent_reservation_state(user)

    available = [
        r for r in matched_researches
        if _match_row_status(
            r, proposed_by_date.get(r.date), today,
            parent_confirmed_ids, parent_pending_ids, parent_canceled_by,
        ) == "available"
    ]

    session_key = f"help_notified_group_{user.id}_{researched_groupe_uid}_{parent_user_id}"
    if not available:
        messages.warning(request, "Aucune date disponible pour ce matching en ce moment.")
    elif request.session.get(session_key, False):
        messages.warning(request, "Vous avez déjà signalé votre disponibilité au parent pour ce matching.")
    else:
        request.session[session_key] = True
        representative = sorted(available, key=lambda r: r.date or today)[0]
        send_help_proposed_bulk_email(representative, [r.date for r in available], user)
        messages.success(request, "Votre aide a été proposée et le parent a été informé par email.")

    return redirect(next_url or fallback_url)

RESERVATIONS_PARTIAL = 'trajects/reservation/partials/reservations_content.html'

_EMPTY_RATING = {'avg': 0, 'count': 0}


def _reservations_param(request, name, default):
    """Lit un paramètre d'écran (onglet, page) en POST d'abord, puis en GET.

    Les actions (confirmer / refuser / annuler) sont des POST HTMX qui repostent
    l'onglet et la pagination en champs cachés : sans ça, le partial re-rendu
    après l'action retomberait sur l'onglet "active", page 1.
    """
    return request.POST.get(name) or request.GET.get(name) or default


def _ratings_by_user(user_ids):
    """Note moyenne + nombre d'avis pour plusieurs utilisateurs, en UNE requête.

    (Les vues de matching font encore un aggregate par match — voir
    my_matchings_proposed ; à factoriser ici le jour où on y touche.)
    """
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = (
        Review.objects.filter(reviewed_user_id__in=ids)
        .values('reviewed_user_id')
        .annotate(avg=Avg('rating'), count=Count('id'))
    )
    return {
        row['reviewed_user_id']: {
            'avg': round(row['avg'] or 0, 1),
            'count': row['count'] or 0,
        }
        for row in rows
    }


def _user_languages(person):
    profile = getattr(person, 'profile', None)
    return profile.languages.all() if profile else []


def _days_since(dt, today):
    """Ancienneté en jours d'une demande — « Demandé il y a 4 jours »."""
    if not dt:
        return None
    return max(0, (today - timezone.localtime(dt).date()).days)


def _coverage_by_research(reservations):
    """Pour chaque date de recherche, qui la couvre et combien de monde est sollicité.

    Un parent peut solliciter plusieurs personnes pour une même date (auto_reserve
    ne dédoublonne que par trajet proposé). Cette carte sert à l'afficher au lieu
    de le laisser invisible : « 3 personnes sollicitées », « déjà couvert par X ».
    """
    coverage = {}
    for r in reservations:
        if not r.researched_traject_id:
            continue
        entry = coverage.setdefault(
            r.researched_traject_id,
            {'confirmed_by_id': None, 'confirmed_name': '', 'pending_count': 0, 'active_count': 0},
        )
        if r.status == 'canceled':
            continue
        entry['active_count'] += 1
        if r.status == 'pending':
            entry['pending_count'] += 1
        elif r.status == 'confirmed' and r.proposed_traject:
            entry['confirmed_by_id'] = r.proposed_traject.user_id
            entry['confirmed_name'] = _display_name_and_initials(r.proposed_traject.user)[0]
    return coverage


def _build_made_reservations(user, today, tab):
    """Demandes envoyées par l'utilisateur (il est le demandeur).

    Groupées par **sa propre recherche** puis par personne sollicitée — le miroir
    exact de _build_received_groups, et le même axe que la page "Mes matchings"
    (my_matchings_researched) d'où partent ces demandes. Regrouper par trajet du
    yaya, comme avant, cassait ce modèle mental d'un écran à l'autre.

    Renvoie (groupes, réservations à plat) — les secondes alimentent le calendrier.
    """
    # Filtre sur la date de la RECHERCHE : l'en-tête du groupe est désormais la
    # recherche, sa plage « Du X au Y » doit correspondre aux lignes affichées.
    # Sans effet pratique : une réservation apparie toujours une proposition et
    # une recherche de même date (cf. _build_match_rows).
    date_filter = (
        {'researched_traject__date__gte': today} if tab == 'active'
        else {'researched_traject__date__lt': today}
    )

    reservations = list(
        # proposed_traject est nullable et, contrairement à researched_traject,
        # n'est pas contraint par le filtre de date : on l'exclut explicitement
        # puisque tout le regroupement déréférence son yaya.
        Reservation.objects.filter(user=user, proposed_traject__isnull=False, **date_filter)
        .select_related(
            'proposed_traject', 'proposed_traject__user', 'proposed_traject__user__profile',
            'proposed_traject__traject',
            'researched_traject', 'researched_traject__traject',
        )
        .prefetch_related(
            'researched_traject__children',
            'researched_traject__children__chld_languages',
            'researched_traject__transport_modes',
            'proposed_traject__transport_modes',
            'proposed_traject__user__profile__languages',
        )
        .order_by('researched_traject__groupe_uid', 'proposed_traject__user_id',
                  'researched_traject__date')
    )

    ratings = _ratings_by_user(r.proposed_traject.user_id for r in reservations)
    coverage = _coverage_by_research(reservations)

    groups = []
    for groupe_uid, group_iter in groupby(reservations, lambda r: str(r.researched_traject.groupe_uid)):
        group_rows = list(group_iter)

        # Représentante du groupe : la recherche de date la plus tôt. Déjà en
        # mémoire via select_related — pas de requête supplémentaire.
        header = min(
            (r.researched_traject for r in group_rows if r.researched_traject.date),
            key=lambda x: x.date,
            default=group_rows[0].researched_traject,
        )

        providers = []
        for yaya_id, provider_iter in groupby(group_rows, lambda r: r.proposed_traject.user_id):
            provider_rows = list(provider_iter)
            proposals = [r.proposed_traject for r in provider_rows if r.proposed_traject.date]
            repr_proposal = (
                min(proposals, key=lambda p: p.date) if proposals
                else provider_rows[0].proposed_traject
            )
            rating = ratings.get(yaya_id, _EMPTY_RATING)

            rows = []
            for r in provider_rows:
                cover = coverage.get(r.researched_traject_id, {})
                # « Déjà couvert » ne concerne que les demandes encore en attente
                # dont la date a été confirmée auprès de quelqu'un d'autre.
                covered_by = (
                    cover.get('confirmed_name')
                    if r.status == 'pending' and cover.get('confirmed_by_id') not in (None, yaya_id)
                    else ''
                )
                rows.append({
                    'reservation': r,
                    'research': r.researched_traject,
                    'proposal': r.proposed_traject,
                    'remaining_places': _available_places(r.proposed_traject),
                    'covered_by': covered_by,
                    'same_date_requests': cover.get('active_count', 1),
                    'requested_days_ago': _days_since(r.reservation_date, today),
                })

            confirmed_count = sum(1 for r in provider_rows if r.status == 'confirmed')
            open_key = f"made:{groupe_uid}:{yaya_id}"
            providers.append({
                'user': repr_proposal.user,
                'display_name': _display_name_and_initials(repr_proposal.user)[0],
                'open_key': open_key,
                'proposed_traject': repr_proposal,
                'traject': repr_proposal.traject,
                # Pas de repli sur les heures de MA recherche : ce sont mes
                # critères, pas l'horaire de la personne. Une offre en rayon
                # n'a ni heure ni destination — on n'affiche alors rien.
                'departure_time': repr_proposal.departure_time,
                'arrival_time': repr_proposal.arrival_time,
                'is_simple': repr_proposal.is_simple,
                'radius_km': repr_proposal.search_radius_km if repr_proposal.is_simple else None,
                'languages': _user_languages(repr_proposal.user),
                'average_rating': rating['avg'],
                'reviews_count': rating['count'],
                'dates_count': len(provider_rows),
                'pending_count': sum(1 for r in provider_rows if r.status == 'pending'),
                'confirmed_count': confirmed_count,
                # L'accord sur l'heure et le lieu exacts se règle par message :
                # on n'ouvre le contact qu'une fois au moins une date confirmée,
                # sinon il n'y a rien à convenir.
                'can_contact': bool(confirmed_count),
                'contact_form': _contact_form_for(open_key) if confirmed_count else None,
                # Le nom du trajet du DESTINATAIRE, pas le mien : c'est lui qui
                # lira le message, et seul son propre nom de série lui permet de
                # situer la conversation dans ses listes.
                'contact_label': repr_proposal.groupe_name or '',
                'rows': rows,
            })

        dates = [r.researched_traject.date for r in group_rows if r.researched_traject.date]
        research_ids = {r.researched_traject_id for r in group_rows}

        groups.append({
            'header': header,
            'stats': {
                'first_date': min(dates) if dates else None,
                'last_date': max(dates) if dates else None,
                'dates_count': len(research_ids),
            },
            'providers': providers,
            'provider_count': len(providers),
            'pending_count': sum(1 for r in group_rows if r.status == 'pending'),
            'confirmed_count': sum(1 for r in group_rows if r.status == 'confirmed'),
            'conflict_dates_count': sum(
                1 for rid in research_ids
                if coverage.get(rid, {}).get('pending_count', 0) > 1
            ),
        })

    groups.sort(key=lambda g: g['stats']['first_date'] or date.min, reverse=(tab == 'history'))
    return groups, reservations


def _build_received_groups(user, today, tab):
    """Demandes reçues sur les trajets proposés par l'utilisateur.

    Deux niveaux, calqués sur les vues de matching pour partager le markup :
    un groupe par trajet proposé (`header` + `stats`), et dans chaque groupe un
    `requester` par parent demandeur (≡ un `match`), porteur de ses dates.
    """
    date_filter = (
        {'researched_traject__date__gte': today} if tab == 'active'
        else {'researched_traject__date__lt': today}
    )

    reservations = list(
        Reservation.objects.filter(proposed_traject__user=user, **date_filter)
        .select_related(
            'user', 'user__profile',
            'proposed_traject', 'proposed_traject__traject',
            'researched_traject', 'researched_traject__traject',
        )
        .prefetch_related(
            'researched_traject__children',
            'researched_traject__children__chld_languages',
            'researched_traject__transport_modes',
            'proposed_traject__transport_modes',
            'user__profile__languages',
        )
        .order_by('proposed_traject__groupe_uid', 'user_id', 'researched_traject__date')
    )

    ratings = _ratings_by_user(r.user_id for r in reservations)

    groups = []
    for groupe_uid, group_iter in groupby(reservations, lambda r: str(r.proposed_traject.groupe_uid)):
        group_rows = list(group_iter)

        # Représentant du groupe : l'occurrence de date la plus tôt. Elle est
        # déjà en mémoire (select_related) — pas de requête supplémentaire.
        header = min(
            (r.proposed_traject for r in group_rows if r.proposed_traject.date),
            key=lambda p: p.date,
            default=group_rows[0].proposed_traject,
        )

        requesters = []
        for parent_id, parent_iter in groupby(group_rows, lambda r: r.user_id):
            parent_rows = list(parent_iter)
            researches = [r.researched_traject for r in parent_rows if r.researched_traject]
            repr_research = min(researches, key=lambda x: x.date or today) if researches else None
            rating = ratings.get(parent_id, _EMPTY_RATING)
            confirmed_count = sum(1 for r in parent_rows if r.status == 'confirmed')
            open_key = f"recv:{groupe_uid}:{parent_id}"
            requesters.append({
                'user': parent_rows[0].user,
                'display_name': _display_name_and_initials(parent_rows[0].user)[0],
                'open_key': open_key,
                'traject': repr_research.traject if repr_research else None,
                # Les heures d'une recherche sont requises en base : pas de repli.
                'departure_time': repr_research.departure_time if repr_research else None,
                'arrival_time': repr_research.arrival_time if repr_research else None,
                'is_simple': False,
                'radius_km': None,
                'languages': _user_languages(parent_rows[0].user),
                'average_rating': rating['avg'],
                'reviews_count': rating['count'],
                'dates_count': len(parent_rows),
                'pending_count': sum(1 for r in parent_rows if r.status == 'pending'),
                'confirmed_count': confirmed_count,
                # Les mêmes enfants reviennent à chaque date : on dédoublonne
                # pour n'afficher la liste qu'une fois sur la carte du parent
                # (même helper que les cartes de matching).
                'children': _distinct_children(
                    r.researched_traject for r in parent_rows if r.researched_traject
                ),
                # Symétrique du côté « envoyées » : le contact ne s'ouvre qu'une
                # fois au moins une date confirmée.
                'can_contact': bool(confirmed_count),
                'contact_form': _contact_form_for(open_key) if confirmed_count else None,
                # Idem : le nom de la recherche du parent, qui est le destinataire.
                'contact_label': (repr_research.groupe_name or '') if repr_research else '',
                'rows': [
                    {
                        'reservation': r,
                        'research': r.researched_traject,
                        'proposal': r.proposed_traject,
                        'remaining_places': _available_places(r.proposed_traject),
                        'requested_days_ago': _days_since(r.reservation_date, today),
                    }
                    for r in parent_rows
                ],
            })

        dates = [r.researched_traject.date for r in group_rows
                 if r.researched_traject and r.researched_traject.date]
        # Une date = une occurrence de ProposedTraject ; on dédoublonne avant de
        # compter les dates complètes / encore ouvertes.
        proposals = {r.proposed_traject_id: r.proposed_traject for r in group_rows}

        groups.append({
            'header': header,
            'stats': {
                'first_date': min(dates) if dates else None,
                'last_date': max(dates) if dates else None,
                'dates_count': len(group_rows),
            },
            'requesters': requesters,
            'requester_count': len(requesters),
            'pending_count': sum(1 for r in group_rows if r.status == 'pending'),
            'confirmed_count': sum(1 for r in group_rows if r.status == 'confirmed'),
            'available_dates_count': sum(1 for p in proposals.values() if _available_places(p) > 0),
            'full_dates_count': sum(1 for p in proposals.values() if _available_places(p) == 0),
        })

    groups.sort(key=lambda g: g['stats']['first_date'] or date.min, reverse=(tab == 'history'))
    return groups, reservations


def _hm(value):
    """Heure au format d'affichage du projet ("08h05"), vide si absente."""
    return value.strftime('%Hh%M') if value else ""


def _avatar_url(person):
    """Photo de profil, ou l'icône générique quand il n'y en a pas."""
    profile = getattr(person, "profile", None)
    picture = getattr(profile, "profile_picture", None)
    if picture:
        try:
            return picture.url
        except ValueError:
            pass
    return static_url('bana/img/icon/Icon_bana.png')


_BADGE_GREY = ("#F3F4F6", "#6B7280")


def _status_badge(reservation, side):
    """Libellé et couleurs du badge de statut, pour le calendrier.

    ⚠ Doit rester aligné sur reservation/partials/status_badge.html, qui fait
    la même chose pour la vue liste. Le calendrier est rendu en JavaScript et
    ne peut pas inclure ce gabarit ; on calcule donc ici plutôt que de
    redéployer la logique une troisième fois en JS.

    `side` vaut "made" (je suis le demandeur) ou "received" (on me sollicite) :
    un refus du conducteur et une annulation du parent valent tous deux
    status='canceled', seul `canceled_by` les distingue.
    """
    if reservation.status == 'confirmed':
        return str(_("Confirmée")), "#D1FAE5", "#065F46"
    if reservation.status == 'pending':
        return str(_("En attente")), "#FEF3C7", "#92400E"

    # Le libellé vient de utils/display.py, partagé avec les emails d'annulation.
    by = reservation.canceled_by
    label = str(cancellation_label(by, side))
    if by == 'yaya' and side == 'made':
        return label, "#FEE2E2", "#991B1B"
    return label, *_BADGE_GREY


_child_labels = child_labels


def _calendar_entries(made_reservations, received_reservations, tab):
    """Entrées du calendrier unifié.

    Les deux flux y cohabitent : une réservation effectuée (la personne affichée
    est le yaya) et une demande reçue (c'est le parent demandeur). Le JS
    (reservations_calendar.js) distingue les deux via la clé `role`.

    Le panneau du jour est actionnable : une date sélectionnée ne porte qu'une
    réservation par personne, donc les réponses y sont unitaires — pas de
    sélection multiple comme dans la vue liste. Les URLs sont calculées ici
    plutôt qu'assemblées en JS : le JS n'a pas à connaître le routage.
    """
    entries = []

    for r in made_reservations:
        pt = r.proposed_traject
        if not pt or not pt.date:
            continue
        person, initials = _display_name_and_initials(pt.user)
        can_act = tab == 'active' and r.status == 'pending'
        badge = _status_badge(r, 'made')
        entries.append({
            "id": r.id,
            "iso": pt.date.isoformat(),
            "role": "made",
            "status": r.status,
            "trip": pt.groupe_name or pt.traject.start_adress,
            "depart": pt.traject.start_adress,
            # Pas de repli sur les heures de MA recherche : ce sont mes critères,
            # pas l'horaire de la personne (même règle que la vue liste).
            "depart_time": _hm(pt.departure_time),
            "arrivee": "" if pt.is_simple else (pt.traject.end_adress or ""),
            "arrivee_time": "" if pt.is_simple else _hm(pt.arrival_time),
            "is_simple": bool(pt.is_simple),
            "radius_km": pt.search_radius_km if pt.is_simple else None,
            # Les enfants d'une demande envoyée sont les siens : rien à apprendre.
            "children": [],
            "person": person,
            "initials": initials,
            "avatar": _avatar_url(pt.user),
            "verified": bool(getattr(getattr(pt.user, 'profile', None), 'prfl_is_verified', False)),
            "can_act": can_act,
            "status_label": badge[0],
            "status_bg": badge[1],
            "status_fg": badge[2],
            "cancel_url": reverse('cancel_reservation', args=[r.id]) if can_act else "",
        })

    for r in received_reservations:
        rt = r.researched_traject
        if not rt or not rt.date:
            continue
        pt = r.proposed_traject
        person, initials = _display_name_and_initials(r.user)
        can_act = tab == 'active' and r.status == 'pending'
        badge = _status_badge(r, 'received')
        entries.append({
            "id": r.id,
            "iso": rt.date.isoformat(),
            "role": "received",
            "status": r.status,
            "trip": (pt.groupe_name or pt.traject.start_adress) if pt else "",
            "depart": rt.traject.start_adress,
            "depart_time": _hm(rt.departure_time),
            "arrivee": rt.traject.end_adress or "",
            "arrivee_time": _hm(rt.arrival_time),
            "is_simple": False,
            "radius_km": None,
            "children": _child_labels(rt),
            "person": person,
            "initials": initials,
            "avatar": _avatar_url(r.user),
            "verified": bool(getattr(getattr(r.user, 'profile', None), 'prfl_is_verified', False)),
            "can_act": can_act,
            "status_label": badge[0],
            "status_bg": badge[1],
            "status_fg": badge[2],
            "accept_url": reverse('manage_reservation', args=[r.id, 'accept']) if can_act else "",
            "reject_url": reverse('manage_reservation', args=[r.id, 'reject']) if can_act else "",
        })

    entries.sort(key=lambda e: e["iso"])
    return entries


def _reservations_context(request, open_key=None):
    """Contexte complet de la page "Mes réservations".

    Partagé par my_reservations et par les actions (manage_reservation,
    cancel_reservation) qui re-rendent le partial en réponse à un POST HTMX.
    `open_key` est la clé du volet à laisser déplié après l'action.
    """
    user = request.user
    today = date.today()

    tab = _reservations_param(request, 'tab', 'active')
    if tab not in ('active', 'history'):
        tab = 'active'

    # Compteurs d'onglets — les deux rôles confondus, un utilisateur pouvant à
    # la fois demander et recevoir. On compte les CARTES effectivement affichées :
    # un groupe de recherche côté demandes envoyées, un groupe de trajet côté reçues.
    def _counts_for(comparison):
        made = (
            Reservation.objects
            .filter(user=user, **{f'researched_traject__date__{comparison}': today})
            .values('researched_traject__groupe_uid').distinct().count()
        )
        received = (
            Reservation.objects
            .filter(proposed_traject__user=user, **{f'researched_traject__date__{comparison}': today})
            .values('proposed_traject__groupe_uid').distinct().count()
        )
        return made + received

    active_count = _counts_for('gte')
    history_count = _counts_for('lt')

    made_groups, made_flat = _build_made_reservations(user, today, tab)
    received_groups, received_flat = _build_received_groups(user, today, tab)

    # Les sections ne dépendent PAS du service : "Proposer un trajet" est ouvert
    # à tout le monde, donc un Parent qui propose reçoit aussi des demandes.
    service = getattr(getattr(user, 'profile', None), 'service', None)
    has_researches = ResearchedTraject.objects.filter(user=user).exists()
    has_proposals = ProposedTraject.objects.filter(user=user).exists()

    show_made = bool(made_groups) or service == 'Parent'
    show_received = bool(received_groups) or service == 'Yaya' or has_proposals

    # États vides actionnables : on pointe vers l'étape suivante réelle de
    # l'utilisateur plutôt que de le laisser sur un cul-de-sac.
    made_empty_cta = (
        {'label': _("Voir mes correspondances"), 'url': reverse('my_matchings_researched')}
        if has_researches
        else {'label': _("Créer une recherche"), 'url': reverse('researched_traject')}
    )
    received_empty_cta = (
        {'label': _("Voir mes trajets proposés"), 'url': reverse('my_proposed_trajects')}
        if has_proposals
        else {'label': _("Proposer un trajet"), 'url': reverse('proposed_traject')}
    )

    return {
        'made_empty_cta': made_empty_cta,
        'received_empty_cta': received_empty_cta,
        'made_reservations': Paginator(made_groups, 10).get_page(
            _reservations_param(request, 'made_page', 1)
        ),
        'received_reservations': Paginator(received_groups, 10).get_page(
            _reservations_param(request, 'received_page', 1)
        ),
        'calendar_entries': _calendar_entries(made_flat, received_flat, tab),
        'show_made': show_made,
        'show_received': show_received,
        'open_key': open_key,
        'is_abonned': Subscription.is_user_abonned(user),
        'tab': tab,
        'active_count': active_count,
        'history_count': history_count,
        'page_title': _("Mes réservations"),
    }


@name_required
def my_reservations(request):
    context = _reservations_context(request)
    if request.htmx:
        return render(request, RESERVATIONS_PARTIAL, context)
    return render(request, 'trajects/reservation/trajets_liste.html', context)
