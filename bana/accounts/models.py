from django.db import models

from django.contrib.auth.models import User


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

    languages = models.ManyToManyField('Languages', blank=True, null=True)
    transport_modes = models.JSONField(default=list, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    #phone = models.CharField(max_length=15, blank=True, null=True)

    # ✅ Champs liés à Stripe Identity
    verified_first_name = models.CharField(max_length=100, blank=True, null=True)
    verified_last_name = models.CharField(max_length=100, blank=True, null=True)
    document_image_url = models.URLField(blank=True, null=True)  # Lien temporaire fourni par Stripe

    def __str__(self):
        return self.user.username

class Languages(models.Model):
    lang_name = models.CharField(max_length=50, unique=True)
    lang_abbr = models.CharField(max_length=2, unique=True)
    
    def __str__(self):
        return self.lang_name


class Child(models.Model):
    class Gender(models.TextChoices):
        GARCON = 'Garçon', 'Garçon'
        FILLE = 'Fille', 'Fille'

    chld_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    chld_name = models.CharField("Nom", max_length=100, blank=False, null=True)
    chld_surname = models.CharField("Prénom", max_length=100, blank=False, null=True)
    chld_birthdate = models.DateField("Date de naissance")
    chld_gender = models.CharField("Genre", max_length=10, choices=Gender.choices, default=Gender.GARCON) # Nouveau champ
    chld_spcl_attention = models.TextField("Attention particulière", blank=True, null=True)
    chld_seat = models.BooleanField("Siège enfant nécessaire", default=False)

    def __str__(self):
        return f"{self.chld_surname} {self.chld_name} (Enfant de {self.chld_user.username})"

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewed_user.username} ({self.rating}/5)"


