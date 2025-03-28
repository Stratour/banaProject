from django import forms
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from django.forms.widgets import SelectMultiple



class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = ['start_adress', 'end_adress','date']
        widgets = {
            'start_adress': forms.TextInput(attrs={
                'id': 'start_adress',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Type a location'
            }),
            'end_adress': forms.TextInput(attrs={
                'id': 'end_adress',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Type a location'
            }),
        }


class ProposedTrajectForm(forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        label="Moyens de transport"
    )
    detour_km = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        label="Détour maximum (km)",
        required=False
    )

    departure_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time',
                   'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time',
                   'placeholder': 'hh:mm'})
    )
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'date-time',
                   'placeholder': 'dd:MM:yyyy'})
    )

    # Ajout des champs de récurrence
    recurrence_type = forms.ChoiceField(
        choices=[
            ('none', 'Aucun'),  # Pas de récurrence
            ('weekly_interval', 'Intervalle hebdomadaire'),  # Répétition hebdomadaire
            ('specific_days', 'Jours spécifiques')  # Répétition sur des jours spécifiques
        ],
        widget=forms.Select(attrs={'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        required=False
    )

    recurrence_interval = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        required=False,
        label="Intervalle (semaines)",
        min_value=1
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=[(str(i), day) for i, day in
                 enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"], 1)],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Jours spécifiques"
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'date'}),
        required=False,
        label="Date de début"
    )

    date_fin = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'date'}),
        required=False,
        label="Date de fin"
    )

    class Meta:
        model = ProposedTraject
        exclude = ['member']
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes',  'detour_km',
                  'number_of_places', 'date',
                  'recurrence_type', 'recurrence_interval', 'tr_weekdays', 'date_debut', 'date_fin']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'number_of_places': 'Nombre de places',
            'date': 'Date du trajet',
            'recurrence_type': 'Type de récurrence',
            'recurrence_interval': 'Intervalle de récurrence (semaines)',
            'tr_weekdays': 'Jours spécifiques',
            'date_debut': 'Date de début de récurrence',
            'date_fin': 'Date de fin de récurrence',
        }
        widgets = {
            'details': forms.Textarea(
                attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                       'placeholder': 'Ajoutez des détails utiles pour les passagers'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialiser les champs de récurrence selon le type sélectionné
        recurrence_type = self.initial.get('recurrence_type', '') or self.instance.recurrence_type

        if recurrence_type == 'weekly_interval':
            self.fields['recurrence_interval'].required = True
            self.fields['tr_weekdays'].required = False
        elif recurrence_type == 'specific_days':
            self.fields['tr_weekdays'].required = True
            self.fields['recurrence_interval'].required = False
        else:
            self.fields['tr_weekdays'].required = False
            self.fields['recurrence_interval'].required = False

class ResearchedTrajectForm(forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        label="Moyens de transport"
    )
    detour_km = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        label="Détour maximum (km)",
        required=False
    )

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    date = forms.DateField(
        widget=forms.DateTimeInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                   'type': 'date-time', 'placeholder': 'dd:MM:yyyy'}),
    )

    class Meta:
        model = ResearchedTraject
        exclude = ['member'] 
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes', 'detour_km', 'number_of_places','date']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'date': 'Date de traject',
        }
        widgets = {    
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour le conducteur'}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['number_of_places']  # On suppose que l'utilisateur n'a besoin que de spécifier le nombre de places
