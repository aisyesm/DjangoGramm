from django import forms


class UserLoginForm(forms.Form):
    email = forms.CharField(label='Email', max_length=100)
    password = forms.CharField(label='Password', max_length=100)


class UserFullInfoForm(forms.Form):
    first_name = forms.CharField(label='First name', max_length=100, min_length=1)
    last_name = forms.CharField(label='Last name', max_length=100, min_length=1)
    bio = forms.CharField(label='Bio', required=False,
                          widget=forms.TextInput(attrs={'placeholder': 'Tell the world something about yourself...'}))
    avatar = forms.ImageField(label='Photo', required=False)