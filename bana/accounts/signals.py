from allauth.account.signals import email_confirmed
from allauth.account.models import EmailAddress
from django.dispatch import receiver

@receiver(email_confirmed)
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
