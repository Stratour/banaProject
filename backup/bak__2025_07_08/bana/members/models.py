from django.db import models
from django.contrib.auth.models import User

GENDER_CHOICES = [
    ("M", "Homme"),
    ("F", "Femme"),
    ("X", "Non Genré"),
]


class Languages(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Members(models.Model):
    memb_user_fk = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="votre username", )
    memb_date_joined = models.DateTimeField(auto_now_add=True)
    memb_birth_date = models.DateField(null=True, blank=True)  # Champ peut être null ou vide
    memb_gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True,
                                   blank=True)
    memb_num_street = models.SmallIntegerField(null=True, blank=True,default=0)
    memb_box = models.CharField(max_length=50, null=True, blank=True)
    memb_street = models.CharField(max_length=50, null=True, blank=True)
    memb_zp = models.SmallIntegerField(null=True, blank=True,default=0)
    memb_num_gsm = models.SmallIntegerField()
    memb_locality = models.CharField(max_length=50, null=True, blank=True)
    memb_country = models.CharField(max_length=50, default='Belgique')
    memb_car = models.BooleanField(default=False)
    # Membres peuvent ne pas avoir de voiture, donc le champ est un booléen (pas de null)
    languages = models.ManyToManyField(Languages, related_name='members', blank=True)  # Les langues peuvent être vides

    def __int__(self):
        return f"{self.memb_user_fk}"


class Type(models.Model):
    memb_type_name = models.CharField(max_length=50)
    memb_type_desc = models.CharField(max_length=255)

    def __int__(self):
        return f"{self.memb_type_name}"


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')  # Celui qui note
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                      related_name='received_reviews')  # Celui qui est noté
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Note de 1 à 5
    comment = models.TextField(blank=True, null=True)  # Optionnel
    created_at = models.DateTimeField(auto_now_add=True)  # Date de la note

    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewed_user.username} ({self.rating}/5)"


'''
class Car
    memb_car_models=

'''
