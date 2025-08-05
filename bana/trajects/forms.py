from django import forms
from accounts.models import Languages, Child
from .models import Traject, ProposedTraject, ResearchedTraject, TransportMode, Reservation
from django.core.exceptions import ValidationError

class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = ['start_adress', 'end_adress','start_cp','end_cp', 'start_locality', 'end_locality',]
        widgets = {
            'start_adress': forms.TextInput(attrs={
                'id': 'start_adress',
                'class': 'w-full p-3 border border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand',
                'placeholder': 'Entrez le point de départ (Adresse, ville, code postal)',
                'autocomplete': 'off'
            }),
            'end_adress': forms.TextInput(attrs={
                'id': 'end_adress',
                'class': 'w-full p-3 border border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand',
                'placeholder': 'Entrez le point d’arrivée (Adresse, ville, code postal)',
                'autocomplete': 'off'
            }),
            
            'start_cp': forms.NumberInput(attrs={
                'id': 'start_cp',
                'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm',
                'placeholder': 'Code postal'
            }),
            'end_cp': forms.NumberInput(attrs={
                'id': 'end_cp',
                'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm',
                'placeholder': 'Code postal'
            }),
            'start_locality': forms.TextInput(attrs={
                'id': 'start_locality',
                'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm',
                'placeholder': 'Ville / Commune'
            }),
            'end_locality': forms.TextInput(attrs={
                'id': 'end_locality',
                'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm',
                'placeholder': 'Ville / Commune'
            }),
        }

class ProposedTrajectForm(forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'inline-flex items-center space-x-1'}),
        label="Moyens de transport",
        required=True,
        error_messages={'required': "Veuillez sélectionner au moins un moyen de transport."}
    )
    
    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'block w-full mt-1 rounded-full border-brand shadow-sm focus:ring-brand focus:border-brand'
        }),
        required=False,
        #empty_label="-- Sélectionnez la langue --",
        label="Langue parlée"
    )

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand',
            'placeholder': 'hh:mm'
        })
    )

    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand',
            'placeholder': 'hh:mm'
        })
    )

    number_of_places = forms.ChoiceField(
        choices=[('', '-- Sélectionnez le nombre de places --')] + ProposedTraject.NUMBER_PLACE,
        widget=forms.Select(attrs={
            'class': 'block w-full mt-1 rounded-full border-brand shadow-sm focus:ring-brand focus:border-brand'
        }),
        required=False,
        label="Nombre de places"
    )
    
    recurrence_type = forms.ChoiceField(
        choices=[
            ('one_week', 'Une fois'),
            ('weekly', 'Toutes les semaines'),
            ('biweekly', 'Une semaine sur deux')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        }),
        required=True,
        initial='one_week'
    )

    recurrence_interval = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm'}),
        required=False,
        label="Intervalle (semaines)",
        min_value=1
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=[(str(i), day) for i, day in
                 enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"], 1)],
        required=False,
        label="Jours spécifiques"
    )
    date_debut = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm', 'type': 'date'}),
        label="Date de début"
    )
    
    def clean_date_debut(self):
        date_debut = self.cleaned_data.get('date_debut')

        if date_debut and date_debut < date.today():
            raise ValidationError("La date de début ne peut pas être antérieure à la date d'aujourd'hui.")

        return date_debut


    date_fin = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm', 'type': 'date'}),
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
                attrs={'class': 'form-input mt-1 block w-full border-brand shadow-sm',
                       'placeholder': 'Ajoutez des détails utiles pour les passagers'}),
        }
    def clean_tr_weekdays(self):
        days = self.cleaned_data.get('tr_weekdays')
        if not days:
            raise forms.ValidationError("Veuillez sélectionner au moins un jour de la semaine.")
        return days
    
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
from datetime import date 
class SimpleProposedTrajectForm(forms.ModelForm):
    # Champs complémentaires (hors modèle)
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'inline-flex items-center space-x-1'}),
        label="Moyens de transport",
        required=True,
        error_messages={'required': "Veuillez sélectionner au moins un moyen de transport."}
    )

    number_of_places = forms.ChoiceField(
        choices=[('', '-- Sélectionnez le nombre de places --')] + ProposedTraject.NUMBER_PLACE,
        widget=forms.Select(attrs={
            'class': 'block w-full mt-1 rounded-full border-brand shadow-sm focus:ring-brand focus:border-brand'
        }),
        required=False,
        label="Nombre de places"
    )
    
    tr_weekdays = forms.ChoiceField(
        choices=[
            ("", "-- Sélectionnez un jour --"),
            ("1", "Lundi"),
            ("2", "Mardi"),
            ("3", "Mercredi"),
            ("4", "Jeudi"),
            ("5", "Vendredi"),
            ("6", "Samedi"),
            ("7", "Dimanche")
        ],
        widget=forms.Select(attrs={
            'class': 'block w-full mt-1 rounded-full border-brand shadow-sm focus:ring-brand focus:border-brand'
        }),
        label="Jour de la semaine",
        required=True
    )
    
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm',
            'type': 'date'
        }),
        label="Date de début"
    )

    def clean_date_debut(self):
        date_debut = self.cleaned_data.get('date_debut')

        if date_debut and date_debut < date.today():
            raise ValidationError("La date de début ne peut pas être antérieure à la date d'aujourd'hui.")

        return date_debut

    class Meta:
        model = Traject
        fields = ['start_adress',"number_of_places"]
        labels = {
            'start_adress': "Ville de départ",
            'number_of_places': 'Nombre de places',
        }
        
        widgets = {
            'start_adress': forms.TextInput(attrs={
                'id': 'start_adress',
                'class': 'w-full p-3 mt-1 border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand',
                'placeholder': 'Entrez le point de départ (Adresse, ville, code postal)',
                'autocomplete': 'on'
            }),
        }

    
class ResearchedTrajectForm(forms.ModelForm):    
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'inline-flex items-center space-x-1'}),
        label="Moyens de transport",
        required=True,
        error_messages={'required': "Veuillez sélectionner au moins un moyen de transport."}
    )

    children = forms.ModelMultipleChoiceField(
        queryset=Child.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'inline-flex items-center space-x-1'}),
        required=True,
        label="Choix du ou des enfants",
        error_messages={'required': "Vous devez sélectionner au moins un enfant."}
    )
 
    
    #detour_distance = forms.FloatField(
    #    widget=forms.NumberInput(attrs={'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm'}),
    #    label="Détour maximum (km)",
    #    required=False
    #)

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full p-3 mt-1 border-brand rounded-full shadow-sm rounded-full focus:ring-brand focus:border-brand',
            'type': 'time',
            'placeholder': 'hh:mm'
        }),
        error_messages={'required': "Veuillez renseigner l'heure de départ."}
    )
    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full p-3 mt-1 border-brand rounded-full shadow-sm rounded-full focus:ring-brand focus:border-brand',
            'type': 'time',
            'placeholder': 'hh:mm'
        }),
        error_messages={'required': "Veuillez renseigner l'heure d’arrivée."}
    )

    recurrence_type = forms.ChoiceField(
        choices=[
            ('one_week', 'Une fois'),
            ('weekly', 'Toutes les semaines'),
            ('biweekly', 'Une semaine sur deux')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        }),
        required=True,
        initial='one_week'
    )

    recurrence_interval = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm'
        }),
        required=False,
        label="Intervalle (semaines)",
        min_value=1
    )
    
    tr_weekdays = forms.MultipleChoiceField(
        choices=[(str(i), day) for i, day in
                 enumerate(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"], 1)],
        required=False,
        label="Jours spécifiques"
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm'
        }),
        required=False
    )
    
    def clean_date_debut(self):
        date_debut = self.cleaned_data.get('date_debut')

        if date_debut and date_debut < date.today():
            raise ValidationError("La date de début ne peut pas être antérieure à la date d'aujourd'hui.")

        return date_debut


    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input mt-1 block w-full rounded-full border-brand shadow-sm'
        }),
        required=False
    )

    class Meta:
        model = ResearchedTraject
        fields = ['departure_time', 'arrival_time', 'transport_modes',
                  'recurrence_type', 'tr_weekdays', 'date_debut', 'date_fin', 'children']
        labels = {
            'departure_time': 'Heure de départ',
            'arrival_time': 'Heure d’arrivée',
            'date': 'Date du trajet',
            'recurrence_type': 'Type de récurrence',
            'date_debut': 'Date de début de récurrence',
            'date_fin': 'Date de fin de récurrence',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        recurrence_type = self.initial.get('recurrence_type', '') or self.data.get('recurrence_type')

        if recurrence_type == 'none':
            self.fields['date_debut'].required = False
            self.fields['date_fin'].required = False
            self.fields['recurrence_interval'].initial = None
        elif recurrence_type in ['weekly', 'biweekly']:
            self.fields['date_debut'].required = True
            self.fields['date_fin'].required = True
            self.fields['recurrence_interval'].initial = 1 if recurrence_type == 'weekly' else 2

        if user:
            self.fields['children'].queryset = Child.objects.filter(chld_user=user)

    def clean_tr_weekdays(self):
        data = self.cleaned_data.get('tr_weekdays')
        if not data:
            raise forms.ValidationError("Veuillez sélectionner au moins un jour de la semaine.")
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        recurrence_type = cleaned_data.get("recurrence_type")
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
    
        if not date_debut:
            self.add_error("date_debut", "Veuillez choisir une date de début.")
    
        if recurrence_type in ['weekly', 'biweekly'] and not date_fin:
            self.add_error("date_fin", "Veuillez choisir une date de fin.")
    
        return cleaned_data

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['number_of_places']  # On suppose que l'utilisateur n'a besoin que de spécifier le nombre de places
