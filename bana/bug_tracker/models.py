from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Component(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Version(models.Model):
    name = models.CharField(max_length=50)
    release_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-release_date']

class Environment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Bug(models.Model):
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
        ('reopened', 'Réouvert'),
        ('duplicate', 'Doublon'),
        ('wont_fix', 'Ne sera pas corrigé'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]
    
    SEVERITY_CHOICES = [
        ('minor', 'Mineur'),
        ('normal', 'Normal'),
        ('major', 'Majeur'),
        ('critical', 'Critique'),
        ('blocker', 'Bloquant'),
    ]
    
    # Informations de base
    title = models.CharField(max_length=200)
    description = models.TextField()
    reproduction_steps = models.TextField(verbose_name="Étapes de reproduction", blank=True, null=True)
    
    # Classification et priorisation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='normal')
    
    # Type de bug
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    affected_version = models.ForeignKey(
        Version, 
        on_delete=models.CASCADE, 
        related_name='affected_bugs',
        verbose_name="Version affectée"
    )
    fixed_version = models.ForeignKey(
        Version, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='fixed_bugs',
        verbose_name="Version corrigée"
    )
    
    # Assignation et suivi
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_bugs',
        verbose_name="Assigné à"
    )
    reported_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='reported_bugs',
        verbose_name="Signalé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Environnement
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    operating_system = models.CharField(max_length=100, verbose_name="Système d'exploitation")
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True, verbose_name="Appareil")
    
    def __str__(self):
        return f"#{self.id} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('bug_tracker:bug_detail', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['-created_at']

class BugAttachment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='bug_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.filename} - Bug #{self.bug.id}"

class BugComment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Commentaire de {self.author.username} sur #{self.bug.id}"
    
    class Meta:
        ordering = ['created_at']

class BugHistory(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field_changed = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"#{self.bug.id} - {self.field_changed} modifié par {self.user.username}"
    
    class Meta:
        ordering = ['-timestamp']
