from django.db import models
from django.contrib.auth.models import User


GENDER_CHOICES = [
    ("M", "Homme"),
    ("F", "Femme"),
    ("X", "Non Genré"),
]

class Members(models.Model):
    memb_user_fk = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="votre username", )
    memb_date_joined = models.DateTimeField(auto_now_add=True)
    memb_birth_date = models.DateField()
    memb_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    memb_num_street = models.SmallIntegerField()
    memb_box = models.CharField(max_length=50)
    memb_street = models.CharField(max_length=50)
    memb_zp = models.SmallIntegerField()
    memb_locality = models.CharField(max_length=50)
    memb_country = models.CharField(max_length=50,default='Belgique')
    memb_car = models.BooleanField(default=False)
    #memb_car_fk=models.OneToOneField(Car, on_delete=models.CASCADE, verbose_name="id de votre voiture", )

    def __int__(self):
        return f"{self.memb_user_fk}"

class Type(models.Model):
    memb_type_name=models.CharField(max_length=50)
    memb_type_desc=models.CharField(max_length=255)

    def __int__(self):
        return f"{self.memb_type_name}"
'''
class Car
    memb_car_models=

'''
