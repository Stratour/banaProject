from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext as _


@receiver(email_confirmed)
def email_confirmed_handler(sender, request, email_address, **kwargs):
    """Source unique de vérité pour la promotion d'un email confirmé.

    Allauth ne met pas à jour `user.email` quand l'adresse confirmée n'est pas
    primary — c'est le cas d'un changement d'email (accounts.views.email_change_confirm).
    On promeut ici la nouvelle adresse et on rétrograde l'ancienne.

    Ne pas dupliquer cette logique dans les vues.
    """
    if email_address.primary:
        # Confirmation d'inscription classique : allauth a déjà tout fait.
        return

    user = email_address.user

    with transaction.atomic():
        # Les anciennes adresses sont SUPPRIMÉES, pas seulement rétrogradées.
        # allauth authentifie sur n'importe quelle EmailAddress correspondante, sans
        # regarder `primary` ni `verified` (voir allauth.account.utils.filter_users_by_email) :
        # une ancienne adresse laissée en base permettrait donc toujours de se connecter.
        user.emailaddress_set.exclude(pk=email_address.pk).delete()

        email_address.primary = True
        email_address.verified = True
        email_address.save(update_fields=['primary', 'verified'])

        user.email = email_address.email
        user.save(update_fields=['email'])

    if request:
        messages.success(request, _("Votre adresse e-mail a été changée avec succès."))
