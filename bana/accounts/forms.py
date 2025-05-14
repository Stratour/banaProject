from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from accounts.models import Profile

'''
class CustomAuthenticationForm(AuthenticationForm):
    print('============ AuthenticationFormLogin =========')

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'form2Example1',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'form2Example2',
        })
    )


class CustomUserCreationForm(UserCreationForm):
    print('============ CustomUserCreationForm =========')

    class Meta:
        model = User  # Associe ce formulaire au modèle User de Django
        fields = ['username', 'email','password1', 'password2']  # Champs inclus dans le formulaire
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username_helptext'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'id_email_helptext'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_password1_helptext'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_password2_helptext'}),
        }
'''

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name'] 

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'phone']