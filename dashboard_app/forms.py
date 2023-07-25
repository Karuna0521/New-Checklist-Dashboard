from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.forms import ModelForm
from .models import User
from .models import QuestionList
from .models import Options
from .models import App_Info


class RegistrationForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'role', 'enable')
        exclude = ['role', 'enable']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'})
        }
        error_messages = {
            'first_name': {'required': ''},
            'last_name': {'required': ''},
            'email': {'required': ''},
            'password': {'required': ''}
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if ' ' in first_name:
            raise forms.ValidationError("First Name should not contain any space")
        else:
            return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if ' ' in last_name:
            raise forms.ValidationError("Last Name should not contain any space")
        else:
            return last_name


class LoginForm(ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'})
        }
        error_messages = {
            'email': {'required': ''},
            'password': {'required': ''}
        }


class AppInfoForm(ModelForm):
    class Meta:
        model = App_Info
        fields = ('app_name', 'package_name', 'main_activity', 'app_version', 'md5', 'sha256', 'app_url')
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control'}),
            'package_name': forms.TextInput(attrs={'class': 'form-control'}),
            'main_activity': forms.TextInput(attrs={'class': 'form-control'}),
            'app_version': forms.TextInput(attrs={'class': 'form-control'}),
            'md5': forms.TextInput(attrs={'class': 'form-control'}),
            'sha256': forms.TextInput(attrs={'class': 'form-control'}),
            'app_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'app_name': {'required': ''},
            'package_name': {'required': ''},
            'main_activity': {'required': ''},
            'app_version': {'required': ''},
            'md5': {'required': ''},
            'sha256': {'required': ''},
            'app_url': {'required': ''}
        }

