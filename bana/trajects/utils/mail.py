import logging
import re
from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from .display import (
    absolute_url,
    cancellation_label,
    child_labels,
    display_name,
    first_name_only,
    format_time,
    traject_parts,
)

logger = logging.getLogger(__name__)

# Repli quand l'identité n'est pas renseignée : jamais l'adresse email, elle ne
# doit se découvrir qu'au moment de répondre. En minuscules pour s'insérer en
# milieu de phrase — les gabarits appliquent |capfirst en tête de phrase, et
# `counterpart_named` leur permet de masquer les tournures où un repli ne veut
# rien dire (« Accompagnateur : un accompagnateur »).
PARENT_FALLBACK = "un parent"
YAYA_FALLBACK = "un accompagnateur"


def _render_html(template_base, context):
    """Rendu HTML d'un email, ou None s'il n'y en a pas — ou s'il casse.

    Le corps texte reste le message : le HTML n'est qu'une alternative. Un
    gabarit HTML absent est un cas normal, et un gabarit HTML cassé ne doit pas
    empêcher le départ d'une notification de réservation. On le journalise donc
    au lieu de laisser l'exception remonter et annuler l'envoi.

    Contrairement à allauth, rien ici ne détecte le .html tout seul : ce dossier
    est rendu à la main, d'où cette fonction.
    """
    try:
        return render_to_string(f"trajects/email/{template_base}_message.html", context)
    except TemplateDoesNotExist:
        return None
    except Exception:
        logger.exception("Rendu HTML impossible pour l'email '%s', envoi en texte seul", template_base)
        return None


def _send(template_base, recipient_email, context, reply_to=None, from_email=None):
    """EmailMultiAlternatives plutôt que send_mail : il sait poser un Reply-To,
    indispensable au message de membre à membre, et attacher la version HTML."""
    if not recipient_email:
        return False
    subject_raw = render_to_string(f"trajects/email/{template_base}_subject.txt", context)
    subject = re.sub(r"\s+", " ", subject_raw.strip())
    message = render_to_string(f"trajects/email/{template_base}_message.txt", context)
    html_message = _render_html(template_base, context)
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            reply_to=[reply_to] if reply_to else None,
        )
        if html_message:
            email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Échec envoi email '%s' à %s", template_base, recipient_email)
        return False


def _reservation_date(reservation):
    """Date d'une réservation : celle du trajet proposé, la recherche du parent
    en repli — `ProposedTraject.date` peut manquer sur d'anciennes lignes."""
    proposed = reservation.proposed_traject
    researched = reservation.researched_traject
    return (proposed.date if proposed else None) or (researched.date if researched else None)


def _horaires(reservation):
    """Heures de départ et d'arrivée, la recherche du parent en repli.

    `ProposedTraject.departure_time` / `arrival_time` sont nullables, ceux de
    `ResearchedTraject` jamais : le repli produit donc toujours une heure réelle
    dès qu'une recherche est liée.
    """
    proposed = reservation.proposed_traject
    researched = reservation.researched_traject
    depart = (proposed.departure_time if proposed else None) or \
             (researched.departure_time if researched else None)
    arrivee = (proposed.arrival_time if proposed else None) or \
              (researched.arrival_time if researched else None)
    return format_time(depart), format_time(arrivee)


def _send_reservation_batch(reservations, template_base, recipient_of,
                            counterpart_of, counterpart_fallback, side):
    """Un seul email par destinataire et par trajet, quel que soit le nombre
    de dates concernées.

    Les actions groupées — un parent qui réserve dix dates d'un coup, un yaya
    qui accepte ou refuse tout un lot — envoyaient auparavant un email par
    date : dix messages identiques à une date près dans la même boîte. Les
    gabarits reçoivent donc toujours une liste `dates` et savent se rendre au
    singulier comme au pluriel.

    Le regroupement inclut le trajet : deux trajets réellement différents
    restent deux emails, même pour la même personne. Il inclut aussi
    `canceled_by`, sinon un lot mixte — un refus du yaya et une annulation en
    cascade dans la même action — produirait un seul mail pour deux motifs
    opposés.

    `counterpart_of` désigne l'autre partie : le yaya pour un mail au parent, le
    parent pour un mail au yaya. `side` suit la même convention que
    `_status_badge` : "made" quand le destinataire est le demandeur, "received"
    quand c'est lui qu'on sollicite.
    """
    batches = {}
    for reservation in reservations:
        recipient = recipient_of(reservation)
        email = getattr(recipient, "email", None)
        proposed = reservation.proposed_traject
        if not email or not proposed:
            continue
        key = (email, proposed.traject_id, reservation.canceled_by)
        batches.setdefault(key, []).append(reservation)

    sent = 0
    for (email, _traject_id, canceled_by), batch in batches.items():
        head = batch[0]
        proposed = head.proposed_traject
        researched = head.researched_traject
        dates = sorted({d for d in (_reservation_date(r) for r in batch) if d})
        heure_depart, heure_arrivee = _horaires(head)
        counterpart = display_name(counterpart_of(head))
        context = {
            "recipient_name": first_name_only(recipient_of(head)),
            "counterpart_name": counterpart or counterpart_fallback,
            "counterpart_named": bool(counterpart),
            "groupe_name": proposed.groupe_name or (researched.groupe_name if researched else ""),
            # Objets `date` et non chaînes : les gabarits les formatent eux-mêmes
            # (« Lun. 12 oct. »), ce qu'un strftime figé ici leur interdirait.
            "dates": dates,
            "dates_count": len(dates),
            "heure_depart": heure_depart,
            "heure_arrivee": heure_arrivee,
            "requested_places": max((r.number_of_places or 0) for r in batch),
            "children": child_labels(researched),
            "canceled_by": canceled_by,
            "cancel_reason": str(cancellation_label(canceled_by, side)),
            "cta_url": absolute_url("my_reservations"),
        }
        context.update(traject_parts(
            proposed.traject, proposed.is_simple, proposed.search_radius_km,
        ))
        if _send(template_base, email, context):
            sent += 1
    return sent


def send_reservation_confirmed_emails(reservations):
    """Confirmation(s) du Yaya : le PARENT est prévenu, en un seul email."""
    return _send_reservation_batch(
        reservations, "reservation_confirmed",
        recipient_of=lambda r: r.user,
        counterpart_of=lambda r: r.proposed_traject.user,
        counterpart_fallback=YAYA_FALLBACK,
        side="made",
    )


def send_reservation_rejected_emails(reservations):
    """Refus du Yaya : le PARENT est prévenu, en un seul email."""
    return _send_reservation_batch(
        reservations, "reservation_rejected",
        recipient_of=lambda r: r.user,
        counterpart_of=lambda r: r.proposed_traject.user,
        counterpart_fallback=YAYA_FALLBACK,
        side="made",
    )


def send_reservation_canceled_emails(reservations):
    """Annulation du côté PARENT : c'est le Yaya qui est prévenu.

    Deux cas bien distincts, que `canceled_by` sépare dans le gabarit : le
    parent a retiré sa demande ('parent'), ou il a confirmé un autre trajet pour
    cette date et Bana a annulé le reste ('auto'). Ne pas confondre avec
    send_reservation_rejected_emails, qui prévient le parent d'un refus du Yaya.
    """
    return _send_reservation_batch(
        reservations, "reservation_canceled",
        recipient_of=lambda r: r.proposed_traject.user,
        counterpart_of=lambda r: r.user,
        counterpart_fallback=PARENT_FALLBACK,
        side="received",
    )


def send_new_reservation_request_emails(reservations):
    """Nouvelle(s) demande(s) du parent : le Yaya reçoit un seul email
    listant les dates demandées."""
    return _send_reservation_batch(
        reservations, "new_reservation_request",
        recipient_of=lambda r: r.proposed_traject.user,
        counterpart_of=lambda r: r.user,
        counterpart_fallback=PARENT_FALLBACK,
        side="received",
    )


def _help_context(research, yaya, dates):
    """Contexte commun aux deux notifications « un accompagnateur est dispo ».

    `ResearchedTraject.departure_time` / `arrival_time` ne sont jamais nuls :
    pas de repli à prévoir ici, contrairement aux emails de réservation.
    """
    yaya_name = display_name(yaya)
    context = {
        "recipient_name": first_name_only(research.user),
        "yaya_name": yaya_name or YAYA_FALLBACK,
        "yaya_named": bool(yaya_name),
        "groupe_name": research.groupe_name or "",
        # Objets `date` : voir _send_reservation_batch.
        "dates": dates,
        "dates_count": len(dates),
        "heure_depart": format_time(research.departure_time),
        "heure_arrivee": format_time(research.arrival_time),
        "children": child_labels(research),
        "cta_url": absolute_url("my_matchings_researched"),
    }
    # Une recherche de parent a toujours une destination : pas de cas `is_simple`.
    context.update(traject_parts(research.traject))
    return context


def send_help_proposed_email(research, yaya):
    """Un yaya se signale sur une date précise : le PARENT est prévenu."""
    dates = [research.date] if research.date else []
    return _send(
        "help_proposed",
        getattr(research.user, "email", None),
        _help_context(research, yaya, dates),
    )


def send_help_proposed_bulk_email(research, dates, yaya):
    """Notification groupée : 1 seul email pour toutes les dates dispo d'un
    matching. `research` est le représentant du lot (la recherche la plus
    ancienne), `dates` les dates réellement disponibles — les lister vaut mieux
    que d'annoncer un simple décompte."""
    return _send(
        "help_proposed_bulk",
        getattr(research.user, "email", None),
        _help_context(research, yaya, sorted(d for d in dates if d)),
    )


def send_member_contact_email(contact_message, sender_name):
    """Message d'un membre à un autre.

    L'expéditeur ne peut pas être le From : le SMTP OVH est authentifié sur
    contact@bana.mobi et tout autre expéditeur serait rejeté par SPF/DKIM. On
    garde donc l'adresse de service, avec le nom de l'expéditeur affiché pour
    que le mail soit reconnaissable, et son adresse en Reply-To : le
    destinataire répond depuis sa boîte et la réponse arrive directement chez
    lui, sans repasser par Bana.

    `sender_name` est calculé par la vue (identité vérifiée quand elle existe)
    et jamais déduit ici : une retombée sur l'adresse email l'afficherait dans
    l'objet du mail, alors qu'elle ne doit se découvrir qu'à la réponse.
    """
    sender = contact_message.sender
    context = {
        "recipient_name": first_name_only(contact_message.recipient),
        "sender_name": sender_name,
        "context_label": contact_message.context_label,
        "body": contact_message.body,
    }
    return _send(
        "member_contact",
        contact_message.recipient.email,
        context,
        reply_to=sender.email,
        from_email=formataddr((f"{sender_name} via Bana", "contact@bana.mobi")),
    )
