from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from accounts.models import Profile, Languages

SERVICE_CHOICES = [
('parent', 'Parent'),
('mentor', 'Mentor'),
]
TRANSPORT_MODES_CHOICES = [
('car', 'Car'),
('bike', 'Bike'),
('public_transport', 'Public Transport'),   
('walking', 'Walking'),
]

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    profile_picture = forms.ImageField(required=False, label='Profile Picture')
    address = forms.CharField(max_length=100, required=False, label='Address (city, country)')

    service = forms.MultipleChoiceField(
        choices=SERVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Services Offered"
    )

    transport_modes = forms.MultipleChoiceField(
        choices=TRANSPORT_MODES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Preferred Transport Modes"
    )

    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        label='Languages Spoken',
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full border rounded px-2 py-1',
            'size': 5
        }),
        required=False
    )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Création du profil lié à l'utilisateur
        profile = Profile.objects.create(
            user=user,
            profile_picture=self.cleaned_data.get('profile_picture'),
            address=self.cleaned_data.get('address'),
            service=self.cleaned_data.get('service', []),
            transport_modes=self.cleaned_data.get('transport_modes', []),
        )

        if self.cleaned_data.get('languages'):
           profile.languages.set(self.cleaned_data['languages'])
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email'] 

class ProfileUpdateForm(forms.ModelForm):
    
    service = forms.MultipleChoiceField(
        choices=SERVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Services proposés/recherchés"
    )

    transport_modes = forms.MultipleChoiceField(
        choices=TRANSPORT_MODES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Modes de transport"
    )

    languages = forms.ModelMultipleChoiceField(
        queryset=Languages.objects.all(),
        widget=forms.SelectMultiple(attrs={'size': 5}),
        required=False,
        label="Langues parlées"
    )
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'phone','address', 'service', 'languages', 'transport_modes', 'bio', ]
        widgets = {
            'service': forms.CheckboxSelectMultiple,
            'transport_modes': forms.CheckboxSelectMultiple,
        }
        
    def clean_service(self):
        return self.cleaned_data['service'] or []

    def clean_transport_modes(self):
        return self.cleaned_data['transport_modes'] or []     
        

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