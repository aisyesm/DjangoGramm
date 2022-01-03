from django.forms import Form, CharField, ImageField, ModelForm, Textarea, PasswordInput, EmailInput, TextInput, FileInput
from .models import User


class UserLoginForm(Form):
    email = CharField(label='', max_length=100, widget=EmailInput(attrs={'placeholder': 'Enter your email',
                                                                         'class': 'form-control'}))
    password = CharField(label='', max_length=100, widget=PasswordInput(attrs={'placeholder': 'Password',
                                                                               'class': 'form-control',
                                                                               'aria-describedby': 'passHelp'}))


class UserRegisterForm(Form):
    email = CharField(label='', max_length=100, widget=EmailInput(attrs={'placeholder': 'Enter your email',
                                                                         'class': 'form-control'}))
    password = CharField(label='', max_length=100, widget=PasswordInput(attrs={'placeholder': 'Password',
                                                                               'class': 'form-control'}))
    confirm_password = CharField(label='', max_length=100,
                                 widget=PasswordInput(attrs={'placeholder': 'Confirm password',
                                                             'class': 'form-control'}))


class UserFullInfoForm(Form):
    first_name = CharField(label='', max_length=30, widget=TextInput(attrs={'placeholder': 'e.g. John',
                                                                            'class': 'form-control'}))
    last_name = CharField(label='', max_length=30, widget=TextInput(attrs={'placeholder': 'e.g. Smith',
                                                                           'class': 'form-control'}))
    bio = CharField(label='Bio', required=False, max_length=400,
                    widget=Textarea(attrs={'placeholder': 'Tell the world something about yourself...',
                                           'class': 'form-control',
                                           'rows': '5'}))
    avatar = ImageField(label='Photo', required=False, widget=FileInput(attrs={'style': 'display: none;',
                                                                               'onchange': 'loadFile(event)'}))


class UserEditInfoForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']

    def __init__(self, initial_values, *args, **kwargs):
        super(UserEditInfoForm, self).__init__(*args, **kwargs)
        self.fields['first_name'] = CharField(initial=initial_values['first_name'], max_length=30)
        self.fields['last_name'] = CharField(initial=initial_values['last_name'], max_length=30)
        self.fields['bio'] = CharField(initial=initial_values['bio'], widget=Textarea(), required=False, max_length=400)
