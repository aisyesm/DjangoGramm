from django.forms import Form, CharField, ImageField, ModelForm, Textarea, TextInput, PasswordInput
from .models import User


class UserLoginForm(Form):
    email = CharField(label='', max_length=100, widget=TextInput(attrs={'placeholder': 'name@domain.com'}))
    password = CharField(label='', max_length=100, widget=PasswordInput())


class UserRegisterForm(Form):
    email = CharField(label='', max_length=100, widget=TextInput(attrs={'placeholder': 'name@domain.com'}))
    password = CharField(label='', max_length=100, widget=PasswordInput())
    confirm_password = CharField(label='', max_length=100, widget=PasswordInput())


class UserFullInfoForm(Form):
    first_name = CharField(label='First name', max_length=30)
    last_name = CharField(label='Last name', max_length=30)
    bio = CharField(label='Bio', required=False, max_length=400,
                          widget=Textarea(attrs={'placeholder': 'Tell the world something about yourself...'}))
    avatar = ImageField(label='Photo', required=False)


class UserEditInfoForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']

    def __init__(self, initial_values, *args, **kwargs):
        super(UserEditInfoForm, self).__init__(*args, **kwargs)
        self.fields['first_name'] = CharField(initial=initial_values['first_name'], max_length=30)
        self.fields['last_name'] = CharField(initial=initial_values['last_name'], max_length=30)
        self.fields['bio'] = CharField(initial=initial_values['bio'], widget=Textarea(), required=False, max_length=400)
