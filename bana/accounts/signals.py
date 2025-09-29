from django.urls import reverse
from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

'''@receiver(email_confirmed)
def clean_and_promote_email(sender, request, email_address, **kwargs):
    user = email_address.user

    # 🔁 Mets à jour l'email principal de l'utilisateur
    user.email = email_address.email
    user.save()

    # ✅ Définit cette adresse comme principale si ce n'est pas déjà fait
    if not email_address.primary:
        email_address.primary = True
        email_address.save()

    # 🧹 Supprime toutes les autres adresses (même si elles sont non vérifiées)
    EmailAddress.objects.filter(user=user).exclude(email=email_address.email).delete()
'''

User = get_user_model()

@receiver(email_confirmed)
def email_confirmed_handler(request, email_address, **kwargs):
    user = email_address.user

    # Ne traiter que les emails secondaires (changement d'email)
    if not email_address.primary:
        # Supprimer l'ancien email principal
        old_primary = user.emailaddress_set.filter(primary=True).first()
        if old_primary:
            old_primary.delete()

        # Promouvoir le nouvel email
        email_address.primary = True
        email_address.verified = True
        email_address.save()

        # Mettre à jour user.email
        user.email = email_address.email
        user.save(update_fields=['email'])

        # Message spécifique au changement d'email
        if request:
            messages.success(request, _("Adresse email changée avec succès."))
            