from datetime import date, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import Languages, Child
from .models import (
    Traject,
    ProposedTraject,
    ResearchedTraject,
    TransportMode,
    Reservation,
)


WEEKDAY_CHOICES = [
    (str(i), day) for i, day in enumerate(
        [_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche")], 1
    )
]

RECURRENCE_CHOICES = [
    ("one_week", _("Trajets occasionnels")),
    ("weekly", _("Trajets chaque semaine")),
    ("biweekly", _("Trajets une semaine sur deux")),
]


class RecurrenceValidationMixin:
    """
    Mixin commun pour uniformiser la validation de la récurrence.
    Utilisé sur ProposedTrajectForm, SimpleProposedTrajectForm
    et ResearchedTrajectForm.
    """

    one_week_label = _("Trajets occasionnels")

    def clean_date_debut(self):
        date_debut = self.cleaned_data.get("date_debut")
        if date_debut and date_debut < date.today():
            raise ValidationError(
                _("La date de début ne peut pas être antérieure à la date d'aujourd'hui.")
            )
        return date_debut

    def clean_tr_weekdays(self):
        days = self.cleaned_data.get("tr_weekdays") or []
        if not days:
            raise ValidationError(
                _("Veuillez sélectionner au moins un jour de la semaine.")
            )
        return days

    def clean(self):
        cleaned_data = super().clean()

        recurrence_type = cleaned_data.get("recurrence_type")
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
        tr_weekdays = cleaned_data.get("tr_weekdays") or []

        # Weekly / biweekly => date_fin obligatoire
        if recurrence_type in ["weekly", "biweekly"] and not date_fin:
            self.add_error("date_fin", _("Veuillez choisir une date de fin."))

        # Si plusieurs jours sont cochés en "one_week", date_fin obligatoire
        if recurrence_type == "one_week" and len(tr_weekdays) > 1 and not date_fin:
            self.add_error(
                "date_fin",
                _("Veuillez choisir une date de fin lorsque plusieurs jours sont sélectionnés.")
            )

        if date_debut and date_fin and date_fin < date_debut:
            self.add_error(
                "date_fin",
                _("La date de fin ne peut pas être antérieure à la date de début.")
            )

        # Limite max à 7 jours pour "one_week"
        if recurrence_type == "one_week" and date_debut and date_fin:
            if (date_fin - date_debut).days > 6:
                self.add_error(
                    "date_fin",
                    _("Pour une récurrence occasionnelle, la période ne peut pas dépasser 7 jours.")
                )

        return cleaned_data
    
class TrajectForm(forms.ModelForm):
    class Meta:
        model = Traject
        fields = [
            "start_adress",
            "end_adress",
            "start_place_id",
            "end_place_id",
        ]
        widgets = {
            "start_adress": forms.TextInput(attrs={
                "id": "start_adress",
                "class": "w-full p-3 border border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand",
                "placeholder": _("Entrez une adresse de départ (Ville, code postal)"),
                "autocomplete": "off",
            }),
            "end_adress": forms.TextInput(attrs={
                "id": "end_adress",
                "class": "w-full p-3 border border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand",
                "placeholder": _("Entrez une adresse d’arrivée (Ville, code postal)"),
                "autocomplete": "off",
            }),
            "start_place_id": forms.HiddenInput(attrs={
                "id": "start_place_id",
            }),
            "end_place_id": forms.HiddenInput(attrs={
                "id": "end_place_id",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_adress = cleaned_data.get("start_adress")
        end_adress = cleaned_data.get("end_adress")
        start_place_id = cleaned_data.get("start_place_id")
        end_place_id = cleaned_data.get("end_place_id")

        if start_adress and not start_place_id:
            self.add_error(
                "start_adress",
                _("Veuillez sélectionner une adresse de départ valide dans la liste."),
            )

        if end_adress and not end_place_id:
            self.add_error(
                "end_adress",
                _("Veuillez sélectionner une adresse d’arrivée valide dans la liste."),
            )

        return cleaned_data

class ProposedTrajectForm(RecurrenceValidationMixin, forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Moyens de transport"),
        required=True,
        error_messages={
            "required": _("Veuillez sélectionner au moins un moyen de transport.")
        },
    )

    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        widget=forms.SelectMultiple(attrs={
            "class": "w-full p-3 border border-brand rounded-2xl shadow-sm focus:ring-brand focus:border-brand"
        }),
        required=False,
        label=_("Langue parlée"),
    )

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            "type": "time",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "placeholder": "hh:mm",
        }),
        error_messages={
            "required": _("Veuillez renseigner l'heure de départ.")
        },
        label=_("Heure de départ"),
    )

    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            "type": "time",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "placeholder": "hh:mm",
        }),
        error_messages={
            "required": _("Veuillez renseigner l'heure d’arrivée.")
        },
        label=_("Heure d’arrivée"),
    )

    number_of_places = forms.ChoiceField(
    choices=[("", _("-- Sélectionnez le nombre de places --"))] + ProposedTraject.NUMBER_PLACE,
    widget=forms.Select(attrs={
        "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand"
    }),
    required=True,
    label=_("Nombre de places"),
    error_messages={
        "required": _("Veuillez sélectionner un nombre de places.")
    },
)

    recurrence_type = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        initial="one_week",
        label=_("Type de récurrence"),
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=True,
        label=_("Jours spécifiques"),
        error_messages={
            "required": _("Veuillez sélectionner au moins un jour de la semaine.")
        },
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "type": "date",
        }),
        required=True,
        label=_("Date de début"),
    )

    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "type": "date",
        }),
        required=False,
        label=_("Date de fin"),
    )

    class Meta:
        model = ProposedTraject
        fields = [
            "details",
            "departure_time",
            "arrival_time",
            "transport_modes",
            "languages",
            "number_of_places",
            "date",
            "recurrence_type",
            "tr_weekdays",
            "date_debut",
            "date_fin",
        ]
        labels = {
            "details": _("Détails"),
            "departure_time": _("Heure de départ"),
            "arrival_time": _("Heure d’arrivée"),
            "number_of_places": _("Nombre de places"),
            "recurrence_type": _("Type de récurrence"),
            "date_debut": _("Date de début de récurrence"),
            "date_fin": _("Date de fin de récurrence"),
        }
        widgets = {
            "details": forms.Textarea(attrs={
                "class": "w-full p-3 border border-brand rounded-2xl shadow-sm focus:ring-brand focus:border-brand min-h-[120px]",
                "placeholder": _("Ajoutez des détails utiles pour les passagers"),
                "rows": 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transport_modes"].label_from_instance = lambda obj: obj.display_name

    def clean_number_of_places(self):
        value = self.cleaned_data.get("number_of_places")
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError(_("Veuillez sélectionner un nombre de places valide."))
        
class SimpleProposedTrajectForm(RecurrenceValidationMixin, forms.ModelForm):
    start_adress = forms.CharField(
        widget=forms.TextInput(attrs={
            "id": "start_adress",
            "class": "w-full p-3 border border-brand shadow-sm rounded-full focus:ring-brand focus:border-brand",
            "placeholder": _("Entrez le point de départ (Adresse, ville, code postal)"),
            "autocomplete": "off",
        }),
        label=_("Ville de départ"),
        required=True,
    )

    start_place_id = forms.CharField(
        widget=forms.HiddenInput(attrs={
            "id": "start_place_id",
        }),
        required=False,
    )

    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Moyens de transport"),
        required=True,
        error_messages={
            "required": _("Veuillez sélectionner au moins un moyen de transport.")
        },
    )

    number_of_places = forms.ChoiceField(
        choices=[("", _("-- Sélectionnez le nombre de places --"))] + ProposedTraject.NUMBER_PLACE,
        widget=forms.Select(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand"
        }),
        required=True,
        label=_("Nombre de places"),
        error_messages={
            "required": _("Veuillez sélectionner un nombre de places.")
        },
    )

    search_radius_km = forms.IntegerField(
        label=_("Rayon de recherche (km)"),
        initial=5,
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "placeholder": "5",
            "min": "1",
            "max": "50",
        }),
        help_text=_("Dans quel rayon souhaitez-vous aider ? (1-50 km)"),
        error_messages={
            "required": _("Veuillez renseigner un rayon de recherche."),
            "min_value": _("Le rayon doit être d’au moins 1 km."),
            "max_value": _("Le rayon ne peut pas dépasser 50 km."),
        },
    )

    recurrence_type = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        initial="one_week",
        label=_("Type de récurrence"),
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=True,
        label=_("Jours spécifiques"),
        error_messages={
            "required": _("Veuillez sélectionner au moins un jour de la semaine.")
        },
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "type": "date",
        }),
        required=True,
        label=_("Date de début"),
    )

    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "type": "date",
        }),
        required=False,
        label=_("Date de fin"),
    )

    class Meta:
        model = ProposedTraject
        fields = [
            "number_of_places",
            "search_radius_km",
            "transport_modes",
            "recurrence_type",
            "tr_weekdays",
            "date_debut",
            "date_fin",
        ]
        labels = {
            "number_of_places": _("Nombre de places"),
            "search_radius_km": _("Rayon de recherche (km)"),
            "recurrence_type": _("Type de récurrence"),
            "date_debut": _("Date de début de récurrence"),
            "date_fin": _("Date de fin de récurrence"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transport_modes"].label_from_instance = lambda obj: obj.display_name

    def clean_start_adress(self):
        value = self.cleaned_data.get("start_adress")
        if not value:
            raise ValidationError(_("Veuillez renseigner une ville de départ."))
        return value

    def clean_number_of_places(self):
        value = self.cleaned_data.get("number_of_places")
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError(_("Veuillez sélectionner un nombre de places valide."))

    def clean(self):
        cleaned_data = super().clean()

        start_adress = cleaned_data.get("start_adress")
        start_place_id = cleaned_data.get("start_place_id")

        if start_adress and not start_place_id:
            self.add_error(
                "start_adress",
                _("Veuillez sélectionner une adresse de départ valide dans la liste."),
            )

        return cleaned_data

class ResearchedTrajectForm(RecurrenceValidationMixin, forms.ModelForm):
    transport_modes = forms.ModelMultipleChoiceField(
        queryset=TransportMode.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Moyens de transport"),
        required=True,
        error_messages={
            "required": _("Veuillez sélectionner au moins un moyen de transport.")
        },
    )

    children = forms.ModelMultipleChoiceField(
        queryset=Child.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Choix du ou des enfants"),
        error_messages={
            "required": _("Vous devez sélectionner au moins un enfant.")
        },
    )

    departure_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            "type": "time",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "placeholder": "hh:mm",
        }),
        error_messages={
            "required": _("Veuillez renseigner l'heure de départ.")
        },
        label=_("Heure de départ"),
    )

    arrival_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            "type": "time",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
            "placeholder": "hh:mm",
        }),
        error_messages={
            "required": _("Veuillez renseigner l'heure d’arrivée.")
        },
        label=_("Heure d’arrivée"),
    )

    recurrence_type = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        initial="one_week",
        label=_("Type de récurrence"),
    )

    tr_weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=True,
        label=_("Jours spécifiques"),
        error_messages={
            "required": _("Veuillez sélectionner au moins un jour de la semaine.")
        },
    )

    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
        }),
        required=True,
        label=_("Date de début"),
    )

    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full p-3 border border-brand rounded-full shadow-sm focus:ring-brand focus:border-brand",
        }),
        required=False,
        label=_("Date de fin"),
    )

    class Meta:
        model = ResearchedTraject
        fields = [
            "departure_time",
            "arrival_time",
            "transport_modes",
            "recurrence_type",
            "tr_weekdays",
            "date_debut",
            "date_fin",
            "children",
        ]
        labels = {
            "departure_time": _("Heure de départ"),
            "arrival_time": _("Heure d’arrivée"),
            "date": _("Date du trajet"),
            "recurrence_type": _("Type de récurrence"),
            "date_debut": _("Date de début de récurrence"),
            "date_fin": _("Date de fin de récurrence"),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["transport_modes"].label_from_instance = lambda obj: obj.display_name

        if user:
            self.fields["children"].queryset = Child.objects.filter(chld_user=user)

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["number_of_places"]