import logging
import re

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send(template_base, recipient_email, context):
    if not recipient_email:
        return False
    subject_raw = render_to_string(f"trajects/email/{template_base}_subject.txt", context)
    subject = re.sub(r"\s+", " ", subject_raw.strip())
    message = render_to_string(f"trajects/email/{template_base}_message.txt", context)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Échec envoi email '%s' à %s", template_base, recipient_email)
        return False


def send_reservation_confirmed_email(reservation):
    context = {
        "trajet_info": str(reservation.proposed_traject.traject),
        "date_str": reservation.proposed_traject.date.strftime("%d/%m/%Y"),
    }
    return _send("reservation_confirmed", reservation.user.email, context)


def send_reservation_rejected_email(reservation):
    context = {
        "trajet_info": str(reservation.proposed_traject.traject),
        "date_str": reservation.proposed_traject.date.strftime("%d/%m/%Y"),
    }
    return _send("reservation_rejected", reservation.user.email, context)


def send_new_reservation_request_email(proposed_traject, requested_places):
    context = {
        "trajet_info": str(proposed_traject.traject),
        "requested_places": requested_places,
    }
    return _send("new_reservation_request", proposed_traject.user.email, context)


def send_help_proposed_email(research):
    context = {
        "trajet_info": str(research.traject),
        "date_str": research.date.strftime("%d/%m/%Y") if research.date else "",
        "heure_depart": research.departure_time.strftime("%H:%M") if research.departure_time else "—",
        "matchings_url": "https://www.bana.mobi/trajets/recherches/matchings/",
    }
    return _send("help_proposed", research.user.email, context)


def send_help_proposed_bulk_email(research, dates_count):
    """Notification groupée (1 seul email pour toutes les dates dispo d'un matching)."""
    context = {
        "trajet_info": str(research.traject),
        "dates_count": dates_count,
        "matchings_url": "https://www.bana.mobi/trajets/recherches/matchings/",
    }
    return _send("help_proposed_bulk", research.user.email, context)
