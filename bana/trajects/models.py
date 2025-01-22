from django.db import models
from members.models import Members

class TransportMode(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Languages(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Traject(models.Model):
    # Adresse en une ligne
    start_adress = models.CharField(max_length=255)
    end_adress = models.CharField(max_length=255)
    
    # Adresse en différentes parties (facultatif)
    start_name = models.CharField(max_length=100, blank=True, null=True)
    start_street = models.CharField(max_length=100, blank=True, null=True)
    start_number = models.CharField(max_length=10, blank=True, null=True)
    start_box = models.CharField(max_length=10, blank=True, null=True)
    start_zp = models.CharField(max_length=10, blank=True, null=True)
    start_locality = models.CharField(max_length=100, blank=True, null=True)
    start_country = models.CharField(max_length=100, default='Belgium', blank=True, null=True)
    start_coordinate = models.CharField(max_length=50, blank=True, null=True)
    
    # Adresse de destination en différentes parties (facultatif)
    end_name = models.CharField(max_length=100, blank=True, null=True)
    end_street = models.CharField(max_length=100, blank=True, null=True)
    end_number = models.CharField(max_length=10, blank=True, null=True)
    end_box = models.CharField(max_length=10, blank=True, null=True)
    end_zp = models.CharField(max_length=10, blank=True, null=True)
    end_locality = models.CharField(max_length=100, blank=True, null=True)
    end_country = models.CharField(max_length=100, default='Belgium', blank=True)
    end_coordinate = models.CharField(max_length=50, blank=True, null=True)
    
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
    NUMBER_PLACE = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')]
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)
    member = models.ForeignKey(Members, related_name='proposed_trajects', on_delete=models.CASCADE)  
    transport_modes = models.ManyToManyField(TransportMode, related_name='proposed_trajects')  
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    language = models.ManyToManyField(Languages, related_name='proposed_trajects',blank=True)
    number_of_places = models.CharField(max_length=1, choices=NUMBER_PLACE)
    details = models.TextField()
    detour_distance = models.FloatField(blank=True, null=True)

    ''' def __str__(self):
            return f"{self.name} by {self.member.memb_user_fk.username}" '''
 
    @classmethod
    def get_proposed_trajects_by_member(cls, member):
        return cls.objects.filter(member=member)

class ResearchedTraject(models.Model):
    NUMBER_PLACE = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')]
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)
    member = models.ForeignKey(Members, related_name='researched_trajects', on_delete=models.CASCADE)
    transport_modes = models.ManyToManyField(TransportMode, related_name='researched_trajects')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    language = models.ManyToManyField(Languages, related_name='researched_trajects',blank=True)
    number_of_places = models.CharField(max_length=1, choices=NUMBER_PLACE)
    details = models.TextField()

    ''' def __str__(self):
            return f"{self.name} by {self.member.memb_user_fk.username}" '''

    @classmethod
    def get_researched_trajects_by_member(cls, member):
        return cls.objects.filter(member=member)

