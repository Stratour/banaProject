from django.db import models
from members.models import Members

class Traject(models.Model):
    start_street = models.CharField(max_length=100, blank=True)
    start_number = models.CharField(max_length=10, blank=True)
    start_box = models.CharField(max_length=10, blank=True)
    start_zp = models.CharField(max_length=10, blank=True)
    start_locality = models.CharField(max_length=100, blank=True)
    start_country = models.CharField(max_length=100, default='Belgium')
    end_street = models.CharField(max_length=100, blank=True)
    end_number = models.CharField(max_length=10, blank=True)
    end_box = models.CharField(max_length=10, blank=True)
    end_zp = models.CharField(max_length=10, blank=True)
    end_locality = models.CharField(max_length=100, blank=True)
    end_country = models.CharField(max_length=100, default='Belgium')
    start_coordinate = models.CharField(max_length=50, blank=True, null=True)
    end_coordinate = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.start_street} to {self.end_street}"

class ProposedTraject(models.Model):
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)
    member = models.ManyToManyField(Members, related_name='proposed_trajects')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    name = models.CharField(max_length=100)
    details = models.TextField()

    def __str__(self):
        members = ", ".join([member.memb_user_fk.username for member in self.member.all()])
        return f"{self.name} by {members}"
    
    @classmethod
    def get_proposed_trajects_by_member(cls, member):
        return cls.objects.filter(member=member)

class ResearchedTraject(models.Model):
    traject = models.ForeignKey(Traject, on_delete=models.CASCADE)
    member = models.ManyToManyField(Members, related_name='researched_trajects')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    name = models.CharField(max_length=100)
    details = models.TextField()

    def __str__(self):
        members = ", ".join([member.memb_user_fk.username for member in self.member.all()])
        return f"{self.name} by {members}"

    @classmethod
    def get_researched_trajects_by_member(cls, member):
        return cls.objects.filter(member=member)

