from django import forms
from .models import Traject, ProposedTraject, ResearchedTraject
from .utils.geocoding import get_coordinate,matrix

class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = [
            'start_street', 'start_number', 'start_box', 'start_zp',
            'start_locality', 'start_country', 'end_street', 'end_number',
            'end_box', 'end_zp', 'end_locality', 'end_country'
        ]

    def clean(self):
        cleaned_data = super().clean()
        start_address = f"{cleaned_data.get('start_street')} {cleaned_data.get('start_number')}, {cleaned_data.get('start_zp')} {cleaned_data.get('start_locality')}"
        start_country = cleaned_data.get('start_country')

        end_address = f"{cleaned_data.get('end_street')} {cleaned_data.get('end_number')}, {cleaned_data.get('end_zp')} {cleaned_data.get('end_locality')}"
        end_country = cleaned_data.get('end_country')

        start_valid, start_coords = get_coordinate(start_address, start_country)
        if not start_valid:
            self.add_error('start_locality', 'Invalid start address. Please verify.')

        end_valid, end_coords = get_coordinate(end_address, end_country)
        if not end_valid:
            self.add_error('end_locality', 'Invalid end address. Please verify.')

        if start_valid and end_valid:
            self.instance.start_coordinate = f"{start_coords[0]},{start_coords[1]}"
            self.instance.end_coordinate = f"{end_coords[0]},{end_coords[1]}"

        return cleaned_data



class ProposedTrajectForm(forms.ModelForm):
    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
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
            'name': forms.TextInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Nom de votre trajet'}),
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour les passagers'}),
        }

class ResearchedTrajectForm(forms.ModelForm):
    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
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
            'name': forms.TextInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Nom de votre recherche'}),
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour le conducteur'}),
        }

class TrajectTypeForm(forms.Form):
    traject_type = forms.ChoiceField(
        choices=[('search', 'Rechercher un trajet'), ('propose', 'Proposer un trajet')],
        widget=forms.RadioSelect(attrs={'class': 'form-radio mt-1 block w-full text-indigo-600'}),
        label="Type de trajet"
    )
