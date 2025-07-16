import dateutil
from dateutil.rrule import rrule, WEEKLY, DAILY
from django.conf import settings
from django.db import models
from members.models import Members
from django.contrib.auth.models import User
from accounts.models import Languages

class TransportMode(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Traject(models.Model):
    # Adresse en une ligne
    start_adress = models.CharField("Adresse de départ (libre)", max_length=255)
    end_adress = models.CharField("Adresse d’arrivée (libre)",max_length=255)

    # Adresse en différentes parties (facultatif)
    start_street = models.CharField("Rue de départ",max_length=100, blank=True, null=True)
    start_cp = models.CharField("Code postal départ",max_length=10, blank=True, null=True)
    start_locality = models.CharField("Ville de départ", max_length=100, blank=True, null=True)

    # Adresse de destination en différentes parties (facultatif)
    end_street = models.CharField("Rue d’arrivée", max_length=100, blank=True, null=True)
    end_cp = models.CharField("Code postal arrivée",max_length=10, blank=True, null=True)
    end_locality = models.CharField("Ville d'arrivée", max_length=100, blank=True, null=True)

    # Coordonnées géographiques (optionnel pour recherche avancée par rayon)
    start_coordinate = models.CharField("Coordonnées départ", max_length=50, blank=True, null=True)
    end_coordinate = models.CharField("Coordonnées arrivée", max_length=50, blank=True, null=True)

    # Pays (valeur par défaut = Belgique)
    start_country = models.CharField(max_length=100, default='Belgium', blank=True, null=True)
    end_country = models.CharField(max_length=100, default='Belgium', blank=True)
    
    # Distance entre le point de départ et d'arrivée (facultatif)
    distance = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.start_adress} to {self.end_adress}"

    def get_coordinate(self):
        return {
            'starting_coordinate': self.start_coordinate,
            'ending_coordinate': self.end_coordinate,
        }

class ProposedTraject(models.Model):
    NUMBER_PLACE = [(str(i), str(i)) for i in range(1, 8)]
        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposed_trajects", null=True, blank=True)
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)

    # Informations de base du trajet
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    number_of_places = models.CharField(max_length=1, choices=NUMBER_PLACE)
    details = models.TextField()
    
    # Modes de transport
    transport_modes = models.ManyToManyField(TransportMode, related_name='proposed_trajects')
    
    # Optionnel : distance de détour accepté
    detour_distance = models.FloatField(blank=True, null=True)
    
    languages = models.ManyToManyField(Languages, related_name='proposed_trajects',blank=True)
    
    recurrence_type = models.CharField(
        max_length=30,
        choices=[
            ('one_week', 'Une semaine seulement'),
            ('weekly', 'Chaque semaine'),
            ('biweekly', 'Une semaine sur deux'),
        ],
        default='none'
    )
    recurrence_interval = models.IntegerField(blank=True, null=True)
    recurrence_days = models.CharField(max_length=255, blank=True, null=True)  # Jours spécifiques (ex: 'MO, WE, FR')

    date = models.DateField(blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.traject.start_adress} → {self.traject.end_adress} ({self.date})"

    @classmethod
    def get_proposed_trajects_by_user(cls, user):
        return cls.objects.filter(user=user)


class ResearchedTraject(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='researched_trajects', null=True, blank=True)
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)
    
    # Informations de base du trajet
    departure_time = models.TimeField()
    arrival_time = models.TimeField()

    # Modes de transport souhaités
    transport_modes = models.ManyToManyField(TransportMode, related_name='researched_trajects')
    
    date = models.DateField(blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    
    recurrence_type = models.CharField(
        max_length=30,
        choices=[
            ('one_week', 'Une semaine seulement'),
            ('weekly', 'Chaque semaine'),
            ('biweekly', 'Une semaine sur deux'),
        ],
        default='none'
    )
    recurrence_interval = models.IntegerField(blank=True, null=True)
    recurrence_days = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - ({self.date}) - {self.traject.start_adress} → {self.traject.end_adress}"

    @classmethod
    def get_researched_trajects_by_user(cls, user):
        return cls.objects.filter(user=user)














class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]

    member = models.ForeignKey(Members, on_delete=models.CASCADE, verbose_name="User who made the reservation")
    # Référence vers l'un ou l'autre des trajets (Proposé ou Recherché)
    traject = models.ForeignKey(
        ProposedTraject,  # Lien vers le modèle Traject (proposé ou recherché)
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    number_of_places = models.CharField(max_length=1,
                                        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                                 ('7', '7')])
    
    
    reservation_date = models.DateTimeField(auto_now_add=True)  # Date et heure de la réservation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Statut de la réservation
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Prix total (par défaut)

    def __str__(self):
        return f"Reservation {self.id} by {self.member.memb_user_fk.username} for {self.number_of_places} places"

    def save(self, *args, **kwargs):
        # Calculer le prix total ici si nécessaire
        self.total_price = int(self.number_of_places) * 20.00  # Exemple de prix par place
        super().save(*args, **kwargs)

    @classmethod
    def get_reservation_by_member(cls, member):
        return cls.objects.filter(member=member)
