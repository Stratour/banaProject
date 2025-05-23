from django import forms
from django.contrib.auth.models import User

from .models import Members, Languages, Review


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            'title': 'Entrez un mot de passe sécurisé',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Mot de passe'
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom d’utilisateur',
            'title': 'Entrez un nom d’utilisateur unique',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Nom d’utilisateur'
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Prénom',
            'title': 'Entrez votre prénom',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Prénom'
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom',
            'title': 'Entrez votre nom',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Nom'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Adresse e-mail',
            'title': 'Entrez une adresse e-mail valide',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Adresse e-mail'
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']


class MembersForm(forms.ModelForm):
    memb_birth_date = forms.DateField(
        required=False,  # Permet de laisser vide
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'Date de naissance',
            'title': 'Entrez votre date de naissance',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Date de naissance'
    )
    memb_gender = forms.ChoiceField(
        required=False,  # Permet de laisser vide
        choices=[('M', 'Homme'), ('F', 'Femme'), ('O', 'Autre')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio mt-1 block w-full text-indigo-600',
        }),
        label='Genre'
    )
    memb_num_street = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro de rue',
            'title': 'Entrez votre numéro de rue',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            'default': '0'
        }),
        label='Numéro de rue'
    )

    def clean_memb_num_street(self):
        value = self.cleaned_data.get('memb_num_street')
        # Si la valeur est vide, on remplace par 0
        if not value:
            return 0  # Ou tout autre valeur par défaut que tu préfères
        return value

    memb_box = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'placeholder': 'Boîte (ex : 4D, Bis)',
            'title': 'Optionnel, indiquez votre boîte',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Boîte'
    )
    memb_street = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'placeholder': 'Rue',
            'title': 'Entrez votre rue',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Rue'
    )
    memb_zp = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'placeholder': 'Code postal',
            'title': 'Entrez votre code postal',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Code postal'
    )

    def clean_memb_zp(self):
        value = self.cleaned_data.get('memb_zp')
        # Si la valeur est vide, on remplace par 0
        if not value:
            return 0
        return value

    memb_num_gsm = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro de GSM',
            'title': 'Entrez votre numéro de GSM',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Numéro de GSM'
    )
    memb_locality = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'placeholder': 'Localité',
            'title': 'Entrez votre ville',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Localité'
    )
    memb_country = forms.CharField(
        required=False,  # Permet de laisser vide
        widget=forms.TextInput(attrs={
            'value': 'Belgique',
            'placeholder': 'Pays',
            'title': 'Pays de résidence',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Pays'
    )
    memb_car = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'title': 'Cochez si vous possédez une voiture',
            'class': 'form-checkbox mt-1 block text-indigo-600',
        }),
        label='Possédez-vous une voiture ?'
    )
    languages = forms.ModelMultipleChoiceField(
        required=False,  # Permet de laisser vide
        queryset=Languages.objects.all(),
        widget=forms.SelectMultiple(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        label='Langues parlées'
    )

    class Meta:
        model = Members
        fields = [
            'memb_birth_date', 'memb_gender', 'memb_num_street', 'memb_box',
            'memb_street', 'memb_zp', 'memb_locality', 'memb_country', 'memb_car', 'languages','memb_num_gsm'
        ]


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom d’utilisateur',
            'title': 'Entrez votre nom d’utilisateur',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Nom d’utilisateur'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            'title': 'Entrez votre mot de passe',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Mot de passe'
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"⭐ {i}") for i in range(1, 6)],
                attrs={
                    'class': 'form-select block w-full mt-1 p-2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-textarea block w-full mt-1 p-2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                    'rows': 4,
                    'placeholder': 'Laissez un commentaire constructif...'
                }
            ),
        }
