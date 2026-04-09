

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
import uuid
from django.contrib.gis.db import models as gis_models
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.CharField(max_length=100, blank=True)
    ci_is_verified = models.BooleanField(default=False)
    bvm_is_verified = models.BooleanField(default=False)
    prfl_is_verified = models.BooleanField(default=False)
    document_bvm = models.FileField(upload_to='bvm/', blank=True, null=True, verbose_name="Bonne vie et moeurs (extrait 596.2, utilisé dans le cadre de l'encadrement de mineurs)")

    service = models.CharField(
        max_length=30,
        blank=False,
        choices=[
            ('Parent', 'Parent'),
            ('Yaya', 'Yaya'),
        ]
    )

    languages = models.ManyToManyField('Languages', blank=True)
    transport_modes = models.JSONField(default=list, blank=True, null=True)
    bio = models.TextField(blank=True, null=True, default="")

    # ✅ Champs liés à Stripe Identity
    verified_first_name = models.CharField(max_length=100, blank=True, null=True)
    verified_last_name = models.CharField(max_length=100, blank=True, null=True)

    onboarding_seen = models.BooleanField(default=False)

    @property
    def trips_count(self):
        from trajects.models import Reservation
        today = timezone.now().date()
        return (
            Reservation.objects
            .filter(
                Q(proposed_traject__user=self.user, proposed_traject__date__lt=today) |
                Q(user=self.user, researched_traject__date__lt=today),
                status='confirmed',
            )
            .distinct()
            .count()
        )

    def update_profile_verified(self):
        is_complete = bool(
            self.profile_picture and
            self.address and
            self.languages.exists()
        )
        if self.prfl_is_verified != is_complete:
            self.prfl_is_verified = is_complete
            self.save(update_fields=['prfl_is_verified'])

    def __str__(self):
        return self.user.username


class Languages(models.Model):
    lang_name = models.CharField(max_length=50, unique=True)
    lang_abbr = models.CharField(max_length=3, unique=True)
    
    class Meta:
        ordering = ["lang_name"]  # ✅ tri alphabétique automatique
        
    def __str__(self):
        return self.lang_name


class Child(models.Model):
    class Gender(models.TextChoices):
        GARCON = 'Garçon', _('Garçon')
        FILLE = 'Fille', _('Fille')

    chld_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    chld_name = models.CharField("Nom", max_length=100, blank=False, null=True)
    chld_surname = models.CharField("Prénom", max_length=100, blank=False, null=True)
    chld_birthdate = models.DateField("Date de naissance")
    chld_gender = models.CharField("Genre", max_length=10, choices=Gender.choices, default=Gender.GARCON)
    
    chld_seat = models.BooleanField("Siège enfant nécessaire", default=False)
    chld_disability = models.BooleanField("Porteur d'un handicap", default=False)
    chld_special_needs = models.TextField("Besoins spécifiques", blank=True, null=True)

    chld_languages = models.ManyToManyField(Languages, blank=True, verbose_name="Langue(s) parlée(s)", related_name="children")
    
    def __str__(self):
        return f"{self.chld_name} {self.chld_surname}"

    @property
    def age(self):
        today = timezone.localdate()
        if not self.chld_birthdate:
            return None
        return today.year - self.chld_birthdate.year - (
            (today.month, today.day) < (self.chld_birthdate.month, self.chld_birthdate.day)
        )

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewed_user.username} ({self.rating}/5)"


class FavoriteAddress(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_addresses")
    
    label = models.CharField(max_length=60, help_text=_("Ex: Maison, École, Sport..."))
    address = models.CharField(max_length=255)
    
    place_id = models.CharField(max_length=255, blank=True, null=True)
    
    point = gis_models.PointField("Coordonnée",srid=4326 ,geography=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]
        unique_together = [("user", "label")]
    
    def __str__(self):
        return f"{self.label} - {self.address}"
    
    @property
    def latitude(self):
        return self.point.y if self.point else None
    
    @property
    def longitude(self):
        return self.point.x if self.point else None
    