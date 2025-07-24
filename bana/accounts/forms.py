from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from accounts.models import Profile, Languages, Child

SERVICE_CHOICES = [
    ('parent', 'Parent'),
    ('yaya', 'Yaya'),
]

TRANSPORT_MODES_CHOICES = [
('car', 'Car'),
('bike', 'Bike'),
('public_transport', 'Public Transport'),   
('walking', 'Walking'),
]

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=False, label='First Name')
    last_name = forms.CharField(max_length=30, required=False, label='Last Name')
    profile_picture = forms.ImageField(required=False, label='Profile Picture')
    address = forms.CharField(max_length=100, required=False, label='Address (city, country)')

    service = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        required=True,
        label="Service",
        widget=forms.Select(attrs={
            'class': 'w-full rounded-full border border-gray-300 bg-white/60 px-4 py-2 text-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand'
        })
    )

    transport_modes = forms.MultipleChoiceField(
        choices=TRANSPORT_MODES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Modes de transport"
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
            service=self.cleaned_data.get('service', ''),
            

            transport_modes=self.cleaned_data.get('transport_modes', []),
        )
        print("DEBUG >>> service =", self.cleaned_data.get('service'))
        profile.save()

        if self.cleaned_data.get('languages'):
           profile.languages.set(self.cleaned_data['languages'])
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email'] 

class ProfileUpdateForm(forms.ModelForm):

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
        

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        # Mettre à jour la liste des champs avec les nouveaux noms et le nouveau champ
        fields = [
            'chld_name', 
            'chld_surname', 
            'chld_birthdate',
            'chld_gender', 
            'chld_spcl_attention', 
            'chld_seat'
        ]
        
        # Mettre à jour le widget pour correspondre au nouveau nom de champ
        widgets = {
            'chld_birthdate': forms.DateInput(attrs={'type': 'date'}),
        }

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
