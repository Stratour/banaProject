from django import forms
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode
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
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    date = forms.DateField(
                widget = forms.DateInput(
                    attrs = {'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                              'type': 'date-time', 'placeholder': 'dd:MM:yyyy'})
        )

    class Meta:
        model = ProposedTraject
        exclude = ['member'] 
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes','language', 'detour_km','number_of_places','date']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'number_of_places':'Nombre de place',
            'language':'language(s)',
            'date': 'Date de traject',
        }
        widgets = {
            'language': SelectMultiple(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour les passagers'}),
        }


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
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes', 'detour_km','language', 'number_of_places','date']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'language':'language(s)',
            'date': 'Date de traject',
        }
        widgets = {    
            'language': SelectMultiple(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour le conducteur'}),
        }

