from django.forms import Form, CharField, ImageField, ModelForm, Textarea, PasswordInput, EmailInput, TextInput, FileInput
from .models import User, Post


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


class UserFullInfoForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserFullInfoForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'first_name': TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'e.g. John',
                                           }),
            'last_name': TextInput(attrs={'class': 'form-control',
                                          'placeholder': 'e.g. Smith',
                                          }),
            'bio': Textarea(attrs={'class': 'form-control',
                                   'rows': '4',
                                   'placeholder': 'Tell the world something about yourself...',
                                   },),
            'avatar': FileInput(attrs={'style': 'display: none;',
                                       'onchange': 'loadFile(event)',
                                       })
        }


class UserAvatarUpdateForm(Form):
    avatar = ImageField(required=True)


class UserEditInfoForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'first_name': TextInput(attrs={'class': 'form-control'}),
            'last_name': TextInput(attrs={'class': 'form-control'}),
            'bio': Textarea(attrs={'class': 'form-control', 'rows': '5'}),
            'avatar': FileInput(attrs={'style': 'display: none;', 'onchange': 'loadFile(event)'})
        }


class UserEditInfoCloudinaryForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar']


class AddPostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['image', 'caption']
        widgets = {
            'image': FileInput(attrs={'class': 'form-control form-control-lg'}),
            'caption': TextInput(attrs={'class': 'form-control'})
        }