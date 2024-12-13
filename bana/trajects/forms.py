from django import forms
from .models import Traject, ProposedTraject, ResearchedTraject

class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = [
            'start_street', 'start_number', 'start_box', 'start_zp',
            'start_locality', 'start_country', 'end_street', 'end_number',
            'end_box', 'end_zp', 'end_locality', 'end_country'
        ]
        labels = {
            'start_street': 'Rue de départ',
            'start_number': 'Numéro de départ',
            'start_box': 'Boîte de départ',
            'start_zp': 'Code postal de départ',
            'start_locality': 'Localité de départ',
            'start_country': 'Pays de départ',
            'end_street': 'Rue d’arrivée',
            'end_number': 'Numéro d’arrivée',
            'end_box': 'Boîte d’arrivée',
            'end_zp': 'Code postal d’arrivée',
            'end_locality': 'Localité d’arrivée',
            'end_country': 'Pays d’arrivée',
        }
        widgets = {
            'start_street': forms.TextInput(attrs={'placeholder': 'Rue de ...'}),
            'start_number': forms.TextInput(attrs={'placeholder': '12'}),
            'start_box': forms.TextInput(attrs={'placeholder': '044, 4D, Bis'}),
            'start_zp': forms.TextInput(attrs={'placeholder': '1000'}),
            'start_locality': forms.TextInput(attrs={'placeholder': 'Bruxelles'}),
            'start_country': forms.TextInput(attrs={'value': 'Belgique', 'placeholder': 'Belgique'}),
            'end_street': forms.TextInput(attrs={'placeholder': 'Rue de ...'}),
            'end_number': forms.TextInput(attrs={'placeholder': '34'}),
            'end_box': forms.TextInput(attrs={'placeholder': '044, 4D, Bis'}),
            'end_zp': forms.TextInput(attrs={'placeholder': '2000'}),
            'end_locality': forms.TextInput(attrs={'placeholder': 'Anvers'}),
            'end_country': forms.TextInput(attrs={'value': 'Belgique', 'placeholder': 'Belgique'}),
        }

class ProposedTrajectForm(forms.ModelForm):
    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'hh:mm'})
    )

    class Meta:
        model = ProposedTraject
        fields = ['name', 'details', 'departure_time', 'arrival_time']
        labels = {
            'name': 'Nom du trajet',
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nom de votre trajet'}),
            'details': forms.Textarea(attrs={'placeholder': 'Ajoutez des détails utiles pour les passagers'}),
        }

class ResearchedTrajectForm(forms.ModelForm):
    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'hh:mm'})
    )

    class Meta:
        model = ResearchedTraject
        fields = ['name', 'details', 'departure_time', 'arrival_time']
        labels = {
            'name': 'Nom de la recherche',
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nom de votre recherche'}),
            'details': forms.Textarea(attrs={'placeholder': 'Ajoutez des détails utiles pour le conducteur'}),
        }

class TrajectTypeForm(forms.Form):
    traject_type = forms.ChoiceField(
        choices=[('search', 'Rechercher un trajet'), ('propose', 'Proposer un trajet')],
        widget=forms.RadioSelect,
        label="Type de trajet"
    )
