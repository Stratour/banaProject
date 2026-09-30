from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import re
import logging
from allauth.account.models import EmailAddress, EmailConfirmation

logger = logging.getLogger(__name__)

def send_change_email_confirmation(request, user, new_email):
    """Envoie un email de confirmation personnalisé pour le changement d'adresse"""
    try:
        email_address = EmailAddress.objects.get(user=user, email=new_email, verified=False)
        
        # Supprimer les anciennes confirmations pour éviter les conflits
        EmailConfirmation.objects.filter(email_address=email_address).delete()
        
        # Créer une nouvelle confirmation et forcer la date d'envoi
        confirmation = EmailConfirmation.create(email_address)
        confirmation.sent = timezone.now()   # ✅ indispensable pour éviter NoneType
        confirmation.save()
        
        # URL d'activation personnalisée
        activate_url = request.build_absolute_uri(
            reverse('accounts:email_change_confirm', args=[confirmation.key])
        )
        
        # Contexte adapté pour tes templates
        context = {
            'user': user,
            'activate_url': activate_url,
            # Le gabarit HTML affiche la nouvelle adresse dans son encadré.
            # allauth nommerait `email` l'adresse destinataire ; ici les deux se
            # confondent, mais la nommer explicitement évite de dépendre de ce
            # hasard le jour où l'envoi changerait de destinataire.
            'new_email': new_email,
            'current_site': {
                'name': request.get_host(),
                'domain': request.get_host()
            },
            'expiration_days': getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3),
        }

        # Seul email de compte à ne pas passer par allauth : `render_mail`
        # attache tout seul le `_message.html` posé à côté du `.txt`, pas
        # `send_mail`. Sans ce `html_message`, déposer le gabarit HTML ne
        # produirait rien et cet email resterait le seul en texte brut.
        html_message = None

        try:
            # Sujet (strip + nettoyage pour éviter newlines)
            subject_raw = render_to_string(
                'account/email/email_change_confirmation_subject.txt', 
                context
            )
            subject = re.sub(r'\s+', ' ', subject_raw.strip())
            
            # Message (hérite de base_message.txt si tu l’utilises)
            message = render_to_string(
                'account/email/email_change_confirmation_message.txt',
                context
            )

            # Le corps texte reste le message ; le HTML n'est qu'une
            # alternative. S'il casse, l'email part quand même — ce lien est la
            # seule façon de valider le changement d'adresse.
            try:
                html_message = render_to_string(
                    'account/email/email_change_confirmation_message.html',
                    context
                )
            except Exception as html_error:
                logger.error(f"HTML template error: {html_error}")
                html_message = None

        except Exception as template_error:
            logger.error(f"Template error: {template_error}")
            # Repli si le gabarit casse : même texte que
            # account/email/email_change_confirmation_message.txt, pour que le
            # membre ne reçoive pas un email d'une autre facture. Le prénom
            # suit la même priorité que base_message.txt — jamais le username,
            # qui n'est pas un nom affichable.
            profile = getattr(user, "profile", None)
            prenom = (profile.verified_first_name if profile else "") or user.first_name
            subject = "Confirmez votre nouvelle adresse e-mail"
            message = f"""Bonjour{f' {prenom}' if prenom else ''},

Vous avez demandé à utiliser cette adresse e-mail pour votre compte Bana.

Confirmez ce changement depuis le lien ci-dessous :

{activate_url}

Tant que ce lien n'est pas ouvert, votre ancienne adresse reste celle de connexion. Une fois le changement confirmé, elle est supprimée et ne permettra plus de vous connecter.

Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail : votre adresse actuelle reste inchangée.

L'équipe Bana"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except EmailAddress.DoesNotExist:
        logger.error(f"EmailAddress not found for user {user.id} and email {new_email}")
        return False
    except Exception as e:
        logger.error(f"Error sending change email confirmation: {str(e)}")
        return False


def send_bvm_rejected_email(user):
    """Prévient le membre que son certificat BVM a été refusé par un admin.

    Appelé depuis bana_admin.views.reject_bvm_prfl, APRÈS la suppression du
    document : le membre doit en redéposer un, d'où le lien vers l'ancre #bvm de
    l'édition du profil.

    L'URL est construite par `absolute_url` (SITE_BASE_URL, préfixe /fr/ forcé)
    et non par la requête : celle-ci est la requête de l'administrateur, et la
    langue active serait la sienne, pas celle du membre.

    Ne lève jamais : un échec d'envoi ne doit pas annuler le refus, déjà
    enregistré. Renvoie True si l'email est parti, pour que la vue puisse le
    signaler à l'administrateur.
    """
    # Import local : accounts ne dépend pas de trajects au chargement.
    from trajects.utils.display import absolute_url

    if not getattr(user, "email", None):
        return False

    context = {
        "user": user,
        "bvm_url": f"{absolute_url('accounts:profile_edit')}#bvm",
    }
    try:
        subject = re.sub(r"\s+", " ", render_to_string(
            "account/email/bvm_rejected_subject.txt", context).strip())
        message = render_to_string("account/email/bvm_rejected_message.txt", context)
        # Le HTML reste une alternative : s'il casse, l'email part en texte.
        try:
            html_message = render_to_string("account/email/bvm_rejected_message.html", context)
        except Exception:
            logger.exception("Rendu HTML impossible pour l'email de refus BVM")
            html_message = None

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'email de refus BVM à l'utilisateur %s", user.pk)
        return False
