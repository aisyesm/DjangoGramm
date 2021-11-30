from django import forms
from django.forms import ModelForm
from .models import User


class UserLoginForm(forms.Form):
    email = forms.CharField(label='Email', max_length=100)
    password = forms.CharField(label='Password', max_length=100)


class UserFullInfoForm(forms.Form):
    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(label='Last name', max_length=100)
    bio = forms.CharField(label='Bio', required=False,
                          widget=forms.Textarea(attrs={'placeholder': 'Tell the world something about yourself...'}))
    avatar = forms.ImageField(label='Photo', required=False)


class UserEditInfoForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']
