from django.db import models

from django.contrib.auth.models import User

# Create your models here.

class UserPayement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    service = models.CharField(max_length=10, choices=[('parent', 'Parent'), ('yaya', 'Yaya')])
    is_active_subscriber = models.BooleanField(default=False)

