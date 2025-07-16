from django import forms
from accounts.models import Languages
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation


class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = ['start_adress', 'end_adress','start_cp','end_cp', 'start_locality', 'end_locality',]
        widgets = {
            'start_adress': forms.TextInput(attrs={
                'id': 'start_adress',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Lieu de départ'
            }),
            'end_adress': forms.TextInput(attrs={
                'id': 'end_adress',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Lieu d\'arrivée'
            }),
            'start_cp': forms.NumberInput(attrs={
                'id': 'start_cp',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Code postal'
            }),
            'end_cp': forms.NumberInput(attrs={
                'id': 'end_cp',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Code postal'
            }),
            'start_locality': forms.TextInput(attrs={
                'id': 'start_locality',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Ville / Commune'
            }),
            'end_locality': forms.TextInput(attrs={
                'id': 'end_locality',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Ville / Commune'
            }),
        }

class ProposedTrajectForm(forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        label="Moyens de transport"
    )
    
    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        label="Langues parlées",
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

    recurrence_type = forms.ChoiceField(
        choices=[
            ('one_week', 'Une semaine seulement'),
            ('weekly', 'Chaques semaines'),
            ('biweekly', 'Une semaine sur deux'),
        ],
        widget=forms.RadioSelect,
        label="Fréquence",
        required=True
    )   

    recurrence_interval = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        required=False,
        label="Intervalle (semaines)",
        min_value=1
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=[(str(i), day) for i, day in
                 enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"], start=1)],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Jours de la semaine"
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'date'}),
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
        fields = ['details', 'departure_time', 'arrival_time', 'transport_modes', 'languages',
                  'number_of_places', 'date',
                  'recurrence_type', 'recurrence_interval', 'date_debut', 'date_fin']
        labels = {
            'details': 'Détails',
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'number_of_places': 'Nombre de places',
            'recurrence_type': 'Type de récurrence',
            'recurrence_interval': 'Intervalle de récurrence (semaines)',
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
        recurrence_type = self.initial.get('recurrence_type', '') or self.data.get('recurrence_type')

        if recurrence_type == 'none':
            self.fields['date_debut'].required = False
            self.fields['date_fin'].required = False
            self.fields['recurrence_interval'].initial = None
        elif recurrence_type in ['weekly', 'biweekly']:
            self.fields['date_debut'].required = True
            self.fields['date_fin'].required = True
            self.fields['recurrence_interval'].initial = 1 if recurrence_type == 'weekly' else 2
        

class ResearchedTrajectForm(forms.ModelForm):    
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        label="Moyens de transport"
    )
    #detour_distance = forms.FloatField(
    #    widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
    #    label="Détour maximum (km)",
    #    required=False
    #)

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'type': 'time', 'placeholder': 'hh:mm'})
    )
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                   'type': 'date', 'placeholder': 'dd:MM:yyyy'}),
    )

    recurrence_type = forms.ChoiceField(
        choices=[
            ('one_week', 'Une semaine seulement'),
            ('weekly', 'Toutes les semaines'),
            ('biweekly', 'Une semaine sur deux')
        ],
        widget=forms.Select(attrs={'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        required=True
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
        model = ResearchedTraject
        fields = ['departure_time', 'arrival_time', 'transport_modes',
                  'recurrence_type', 'date_debut', 'date_fin']
        labels = {
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'date': 'Date du trajet',
            'recurrence_type': 'Type de récurrence',
            'date_debut': 'Date de début de récurrence',
            'date_fin': 'Date de fin de récurrence',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Initialiser les champs de récurrence selon le type sélectionné
        recurrence_type = self.initial.get('recurrence_type', '') or self.data.get('recurrence_type')

        if recurrence_type == 'none':
            self.fields['date_debut'].required = False
            self.fields['date_fin'].required = False
            self.fields['recurrence_interval'].initial = None
        elif recurrence_type in ['weekly', 'biweekly']:
            self.fields['date_debut'].required = True
            self.fields['date_fin'].required = True
            self.fields['recurrence_interval'].initial = 1 if recurrence_type == 'weekly' else 2


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['number_of_places']  # On suppose que l'utilisateur n'a besoin que de spécifier le nombre de places
