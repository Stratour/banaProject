from django.db import models

from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    image = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username