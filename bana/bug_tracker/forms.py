# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Bug, BugComment, BugAttachment, Component, Version, Environment

class BugForm(forms.ModelForm):
    class Meta:
        model = Bug
        fields = [
            'title', 'description', 'reproduction_steps',
            'status', 'priority', 'severity',
            'component', 'affected_version', 'fixed_version',
            'assigned_to', 'environment', 'operating_system',
            'browser', 'device'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du bug'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du bug'
            }),
            'reproduction_steps': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Étapes pour reproduire le bug'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'component': forms.Select(attrs={'class': 'form-select'}),
            'affected_version': forms.Select(attrs={'class': 'form-select'}),
            'fixed_version': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'environment': forms.Select(attrs={'class': 'form-select'}),
            'operating_system': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: Windows 11, macOS 14.0, Ubuntu 22.04'
            }),
            'browser': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: Chrome 120.0, Firefox 121.0'
            }),
            'device': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: Desktop, iPhone 15, Samsung Galaxy S24'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limiter les utilisateurs assignables aux utilisateurs actifs
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].empty_label = "Non assigné"
        self.fields['fixed_version'].empty_label = "Non définie"

class BugCommentForm(forms.ModelForm):
    class Meta:
        model = BugComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ajouter un commentaire...'
            })
        }

class BugAttachmentForm(forms.ModelForm):
    class Meta:
        model = BugAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.gif,.pdf,.txt,.log,.zip'
            })
        }

class BugFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Tous les statuts')] + Bug.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'Toutes les priorités')] + Bug.PRIORITY_CHOICES
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans le titre ou la description...',
            'hx-get': '.',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#bug-table',
            'hx-include': '#filter-form'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '.',
            'hx-trigger': 'change',
            'hx-target': '#bug-table',
            'hx-include': '#filter-form'
        })
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '.',
            'hx-trigger': 'change',
            'hx-target': '#bug-table',
            'hx-include': '#filter-form'
        })
    )
    
    component = forms.ModelChoiceField(
        queryset=Component.objects.all(),
        required=False,
        empty_label="Tous les composants",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '.',
            'hx-trigger': 'change',
            'hx-target': '#bug-table',
            'hx-include': '#filter-form'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les assignés",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '.',
            'hx-trigger': 'change',
            'hx-target': '#bug-table',
            'hx-include': '#filter-form'
        })
    )

class QuickAssignForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Non assigné",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'hx-post': '',
            'hx-trigger': 'change',
            'hx-target': 'closest .assignee-container'
        })
    )

class QuickStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Bug.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'hx-post': '',
            'hx-trigger': 'change',
            'hx-target': 'closest .status-container'
        })
    )
