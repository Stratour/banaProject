from django import forms
from django.contrib.auth.models import User

from .models import Members, Languages


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
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'Date de naissance',
            'title': 'Entrez votre date de naissance',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Date de naissance'
    )
    memb_gender = forms.ChoiceField(
        choices=[('M', 'Homme'), ('F', 'Femme'), ('O', 'Autre')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio mt-1 block w-full text-indigo-600',
        }),
        label='Genre'
    )
    memb_num_street = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro de rue',
            'title': 'Entrez votre numéro de rue',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Numéro de rue'
    )
    memb_box = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Boîte (ex : 4D, Bis)',
            'title': 'Optionnel, indiquez votre boîte',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Boîte'
    )
    memb_street = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Rue',
            'title': 'Entrez votre rue',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Rue'
    )
    memb_zp = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Code postal',
            'title': 'Entrez votre code postal',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Code postal'
    )
    memb_locality = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Localité',
            'title': 'Entrez votre ville',
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
        }),
        label='Localité'
    )
    memb_country = forms.CharField(
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
        queryset=Languages.objects.all(),
        widget=forms.SelectMultiple(
            attrs={'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        label='Langues parlées'
    )

    class Meta:
        model = Members
        fields = [
            'memb_birth_date', 'memb_gender', 'memb_num_street', 'memb_box',
            'memb_street', 'memb_zp', 'memb_locality', 'memb_country', 'memb_car','languages'
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
