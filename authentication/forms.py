from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import *

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=50)
    password1 = forms.CharField(max_length=50)
    password2 = forms.CharField(max_length=50)
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        ]

class AuthorizationForm(forms.ModelForm):
    class Meta:
        model = Authorization
        fields = "__all__"
        exclude = ["user"]