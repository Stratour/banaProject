from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.product_name} - {'Actif' if self.is_active else 'Inactif'}"
    
    # Méthode de classe pour vérifier l'abonnement
    # Dans views.py
    # from stripe_sub.models import Subscription
    # is_abonned = Subscription.is_user_abonned(user)

    @classmethod
    def is_user_abonned(cls, user_instance):
        """
        Vérifie si l'utilisateur a un abonnement actif.
        Renvoie True ou False.
        """
        if user_instance is None or not user_instance.is_authenticated:
            return False
            
        return cls.objects.filter(user=user_instance, is_active=True).exists()
    
    #def check_if_expired(self):
    #    from django.utils import timezone
    #    if self.current_period_end and self.current_period_end < timezone.now():
    #        self.is_active = False
    #        self.save()
