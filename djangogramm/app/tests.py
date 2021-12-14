import re

from django.test import TestCase, Client
from django.core import mail

from .models import User
from .views import Authentication, UserEnterInfoView, Feed, Register
from .forms import UserLoginForm, UserRegisterForm


class AuthenticationViewTestCase(TestCase):
    def setUp(self):
        self.c = Client()

    def test_get(self):
        """Renders correct view and template."""
        response = self.c.get('/app/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')

    def test_login_wrong_credentials(self):
        """Login with incorrect credentials."""
        data = {'email': 'incorrect', 'password': 'incorrect', 'proceed': 'login'}
        self.assertTrue(UserLoginForm(data=data).is_valid())
        response = self.c.post('/app/', data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')
        self.assertTrue(response.context.get('invalid_credentials'))

    def test_enter_info(self):
        """Login user that does not have first_name and last_name set."""
        user = User.objects.create_user(email='test1', password='test', is_active=True)
        data = {'email': user.email, 'password': 'test', 'proceed': 'login'}
        response = self.c.post('/app/', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, UserEnterInfoView.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/user_enter_info.html')

    def test_login(self):
        """Login with full info set."""
        user = User.objects.create_user(email='test2', password='test', is_active=True,
                                        first_name='test', last_name='test')
        data = {'email': user.email, 'password': 'test', 'proceed': 'login'}
        response = self.c.post('/app/', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Feed.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/feed.html')


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.c = Client()

    def test_get(self):
        """Renders correct view and template."""
        response = self.c.get('/app/register', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Register.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/register.html')

    def test_confirm_password(self):
        """Not providing a confirm password or providing a different value."""
        data = {'email': 'test', 'password': 'test', 'proceed': 'register'}
        self.assertFalse(UserRegisterForm(data=data).is_valid())

        data = {'email': 'test@mail.ru', 'password': 'test', 'confirm_password': 'dont_match', 'proceed': 'register'}
        self.assertTrue(UserRegisterForm(data=data).is_valid())
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('passwords_dont_match'))

    def test_invalid_email(self):
        """Try to register with invalid email."""
        data = {'email': 'test', 'password': 'test', 'confirm_password': 'test', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('invalid_email'))

    def test_already_registered(self):
        """Try to register with already used email."""
        user = User.objects.create_user(email='exists@gmail.com', password='test', is_active=True,
                                        first_name='test', last_name='test')
        data = {'email': user.email, 'password': 'bla', 'confirm_password': 'bla', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('user_already_exist'))

    def test_register_and_activate_user(self):
        """Check if user can be registered and activated with an activation link from email."""
        data = {'email': 'test@mail.ru', 'password': 'test', 'confirm_password': 'test', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate your DjangoGramm account.')
        self.assertTemplateUsed(response=response, template_name='app/acc_active_email.html')
        self.assertTemplateUsed(response=response, template_name='app/activation_link_sent.html')
        user = User.objects.filter(email=data['email']).first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)

        # lets activate user
        pattern = r'app/activate/(\S+)/(\S+)'
        activation_link = re.search(pattern, mail.outbox[0].body)
        uidb64, token = activation_link.group(1), activation_link.group(2)
        response = self.c.get(f'/app/activate/{uidb64}/{token}', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, UserEnterInfoView.as_view().__name__)
        user = User.objects.filter(email=data['email']).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
