from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from accounts.models import Profile, Languages, Child, Review


SERVICE_CHOICES = [
    ('Parent', 'Parent'),
    ('Yaya', 'Yaya'),
]

TRANSPORT_MODES_CHOICES = [
    ('car', 'Voiture'),
    ('bike', 'Vélo'),
    ('public_transport', 'Transport en commun'),
    ('walking', 'À pied'),
]


# ---------- Mixin : règles globales ----------
class TailwindFormMixin:
    """
    Règles:
      - Inputs (Text/Email/Password/Date/Time/Number...)  -> rounded-full
      - Select / SelectMultiple / Textarea                 -> rounded-none
      - Checkbox / CheckboxSelectMultiple                  -> form-checkbox h-5 w-5 text-brand (pas de w-full)
    Si un widget a déjà 'class', on le respecte (pas d'écrasement).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base_input = "mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand"
        base_select = "mt-1 w-full border border-brand px-4 py-2 bg-white shadow-sm focus:ring-brand focus:border-brand rounded-none"
        base_textarea = "mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-none"
        base_checkbox = "form-checkbox h-5 w-5 text-brand"

        for name, field in self.fields.items():
            w = field.widget

            # Ne pas écraser si classes déjà posées explicitement
            if "class" in w.attrs:
                continue

            # Checkboxes (unitaire)
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = base_checkbox
                continue

            # Groupes de checkboxes
            if isinstance(w, forms.CheckboxSelectMultiple):
                # Django appliquera cette classe aux <input type="checkbox"> enfants
                w.attrs["class"] = base_checkbox
                continue

            # Selects (liste déroulante)
            if isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = base_select
                continue

            # Textarea
            if isinstance(w, forms.Textarea):
                w.attrs["class"] = base_textarea
                continue

            # Autres (inputs classiques)
            w.attrs["class"] = f"{base_input} rounded-full"


# ---------- Signup ----------
class CustomSignupForm(TailwindFormMixin, SignupForm):
    first_name = forms.CharField(max_length=30, required=False, label='First Name')
    last_name = forms.CharField(max_length=30, required=False, label='Last Name')
    profile_picture = forms.ImageField(required=False, label='Profile Picture')
    address = forms.CharField(max_length=100, required=False, label='code postal, ville')

    service = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        required=True,
        label="Service",
        # SELECT => no rounded
        widget=forms.Select(attrs={
            'class': 'mt-1 w-full border border-brand px-4 py-2 bg-white shadow-sm focus:ring-brand focus:border-brand rounded-none'
        })
    )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        profile = Profile.objects.create(
            user=user,
            profile_picture=self.cleaned_data.get('profile_picture'),
            address=self.cleaned_data.get('address'),
            service=self.cleaned_data.get('service', ''),
        )
        profile.save()

        if self.cleaned_data.get('languages'):
            profile.languages.set(self.cleaned_data['languages'])
        return user


# ---------- User update ----------
class UserUpdateForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        # Mixin applique rounded-full aux inputs, pas d'arrondi aux select/textarea (si un jour tu en ajoutes)


# ---------- Profile update ----------
class ProfileUpdateForm(TailwindFormMixin, forms.ModelForm):
    transport_modes = forms.MultipleChoiceField(
        choices=TRANSPORT_MODES_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-5 w-5 text-brand'
        }),
        required=False,
        label="Modes de transport"
    )

    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        # SELECT multiple => no rounded
        widget=forms.SelectMultiple(attrs={
            'size': 5,
            'class': 'mt-1 w-full border border-brand px-4 py-2 bg-white shadow-sm focus:ring-brand focus:border-brand rounded-none'
        }),
        required=False,
        label="Langues parlées"
    )

    class Meta:
        model = Profile
        fields = ['profile_picture', 'address', 'languages', 'transport_modes', 'bio', 'document_bvm']
        widgets = {
            # TEXTAREA => no rounded
            'bio': forms.Textarea(attrs={
                'class': 'mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-none',
                'rows': 5,
                'placeholder': "Présente-toi en quelques lignes..."
            }),
        }


# ---------- Child ----------
class ChildForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Child
        fields = [
            'chld_name',
            'chld_surname',
            'chld_birthdate',
            'chld_gender',
            'chld_spcl_attention',
            'chld_seat'
        ]
        widgets = {
            # Inputs => rounded-full (mixin aussi, mais on laisse explicite ici)
            'chld_name': forms.TextInput(attrs={
                'class': 'mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-full'
            }),
            'chld_surname': forms.TextInput(attrs={
                'class': 'mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-full'
            }),
            'chld_birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-full'
            }),
            # Select => no rounded
            'chld_gender': forms.Select(attrs={
                'class': 'mt-1 w-full border border-brand px-4 py-2 bg-white shadow-sm focus:ring-brand focus:border-brand rounded-none'
            }),
            # Textarea => no rounded
            'chld_spcl_attention': forms.Textarea(attrs={
                'class': 'mt-1 w-full border border-brand px-4 py-2 shadow-sm focus:ring-brand focus:border-brand rounded-none',
                'rows': 3,
                'placeholder': 'Indiquez les besoins particuliers éventuels...'
            }),
            # Checkbox => pas de w-full
            'chld_seat': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-brand'
            }),
        }


# ---------- Review ----------
class ReviewForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"⭐ {i}") for i in range(1, 6)],
                attrs={
                    'class': 'mt-1 w-full border border-gray-300 p-2 bg-white shadow-sm focus:ring-brand focus:border-brand rounded-md'
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'mt-1 w-full border border-gray-300 p-2 shadow-sm focus:ring-brand focus:border-brand rounded-md',
                    'rows': 4,
                    'placeholder': 'Laissez un commentaire constructif...'
                }
            ),
        }
