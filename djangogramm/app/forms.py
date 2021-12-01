from django.forms import Form, CharField, ImageField, ModelForm, Textarea
from .models import User


class UserLoginForm(Form):
    email = CharField(label='Email', max_length=100)
    password = CharField(label='Password', max_length=100)


class UserFullInfoForm(Form):
    first_name = CharField(label='First name', max_length=100)
    last_name = CharField(label='Last name', max_length=100)
    bio = CharField(label='Bio', required=False,
                          widget=Textarea(attrs={'placeholder': 'Tell the world something about yourself...'}))
    avatar = ImageField(label='Photo', required=False)


class UserEditInfoForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']

    def __init__(self, initial_values, *args, **kwargs):
        super(UserEditInfoForm, self).__init__(*args, **kwargs)
        self.fields['first_name'] = CharField(initial=initial_values['first_name'])
        self.fields['last_name'] = CharField(initial=initial_values['last_name'])
        self.fields['bio'] = CharField(initial=initial_values['bio'], widget=Textarea(), required=False)
