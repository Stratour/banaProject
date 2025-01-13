from django import forms
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode
from .utils.geocoding import get_coordinate, matrix

class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = [
            'start_name','start_street', 'start_number', 'start_box', 'start_zp',
            'start_locality', 'start_country','end_name', 'end_street', 'end_number',
            'end_box', 'end_zp', 'end_locality', 'end_country'
        ]

    def clean(self):
        cleaned_data = super().clean()
        start_address = f"{cleaned_data.get('start_name')}, {cleaned_data.get('start_street')} {cleaned_data.get('start_number')}, {cleaned_data.get('start_zp')} {cleaned_data.get('start_locality')}"
        start_country = cleaned_data.get('start_country')

        end_address = f"{cleaned_data.get('start_name')}, {cleaned_data.get('end_street')} {cleaned_data.get('end_number')}, {cleaned_data.get('end_zp')} {cleaned_data.get('end_locality')}"
        end_country = cleaned_data.get('end_country')

        start_valid, start_coords = get_coordinate(start_address, start_country)
        if not start_valid:
            self.add_error('start_locality', 'Adresse de départ invalide. Veuillez vérifier.')

        end_valid, end_coords = get_coordinate(end_address, end_country)
        if not end_valid:
            self.add_error('end_locality', 'Adresse d’arrivée invalide. Veuillez vérifier.')

        if start_valid and end_valid:
            self.instance.start_coordinate = f"{start_coords[0]},{start_coords[1]}"
            self.instance.end_coordinate = f"{end_coords[0]},{end_coords[1]}"
        '''
            # Calcul de la distance via Matrix API
            distance = matrix(start_coords, end_coords)
            if distance:
                self.instance.distance = distance
        '''
        return cleaned_data


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

    class Meta:
        model = ProposedTraject
        exclude = ['member'] 
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes', 'detour_km','language','number_of_places']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
        }
        widgets = {
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

    class Meta:
        model = ResearchedTraject
        exclude = ['member'] 
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes', 'detour_km', 'language', 'number_of_places']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
        }
        widgets = {
            'details': forms.Textarea(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'placeholder': 'Ajoutez des détails utiles pour le conducteur'}),
        }
