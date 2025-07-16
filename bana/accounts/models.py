from django.db import models

from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.CharField(max_length=100, blank=True)
    
    
    service = models.JSONField(default=list, blank=True)
    languages = models.ManyToManyField('Languages', blank=True)
    transport_modes = models.JSONField(default=list, blank=True)
    
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username
    
class Languages(models.Model):
    lang_name = models.CharField(max_length=50, unique=True)
    lang_abbr = models.CharField(max_length=2, unique=True)
    
    def __str__(self):
        return self.lang_name

