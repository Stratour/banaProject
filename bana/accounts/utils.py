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
            'current_site': {
                'name': request.get_host(),
                'domain': request.get_host()
            },
            'expiration_days': getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3),
        }
        
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
            
        except Exception as template_error:
            logger.error(f"Template error: {template_error}")
            # Fallback simple
            subject = "Changement d'adresse Email"
            message = f"""Bonjour {user.first_name or user.username},

Vous avez demandé à changer votre adresse e-mail sur {request.get_host()}.

Pour confirmer ce changement, cliquez sur le lien ci-dessous :
{activate_url}

Si vous n'avez pas demandé ce changement, ignorez cet email.

L'équipe de {request.get_host()}"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            fail_silently=False,
        )
        
        return True
        
    except EmailAddress.DoesNotExist:
        logger.error(f"EmailAddress not found for user {user.id} and email {new_email}")
        return False
    except Exception as e:
        logger.error(f"Error sending change email confirmation: {str(e)}")
        return False
