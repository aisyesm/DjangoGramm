from django.test import TestCase, Client
from django.core import mail

from .models import User
from .views import Authentication, UserEnterInfoView, Feed, Register
from .forms import UserLoginForm, UserRegisterForm


class AuthenticationViewTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(email='test1', password='test', is_active=True)
        self.user_with_full_name = User.objects.create_user(email='test2', password='test', is_active=True,
                                                            first_name='test', last_name='test')

    def test_get(self):
        """Renders correct view and template."""
        response = self.c.get('/app/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')

    def test_post(self):
        """Login existing user or reload template with invalid credentials."""

        # login with incorrect credentials
        data = {'email': 'incorrect', 'password': 'incorrect', 'proceed': 'login'}
        self.assertTrue(UserLoginForm(data=data).is_valid())
        response = self.c.post('/app/', data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')
        self.assertTrue(response.context.get('invalid_credentials'))

        # login with correct credentials but without full info set
        data = {'email': 'test1', 'password': 'test', 'proceed': 'login'}
        response = self.c.post('/app/', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, UserEnterInfoView.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/user_enter_info.html')

        # login with full info set
        data = {'email': 'test2', 'password': 'test', 'proceed': 'login'}
        response = self.c.post('/app/', data=data, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Feed.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/feed.html')


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.existing_user = User.objects.create_user(email='exists@gmail.com', password='test', is_active=True,
                                                            first_name='test', last_name='test')

    def test_get(self):
        """Renders correct view and template."""
        response = self.c.get('/app/register', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Register.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/register.html')

    def test_post(self):
        """Register a new user."""

        # try to register without confirming password
        data = {'email': 'test', 'password': 'test', 'proceed': 'register'}
        self.assertFalse(UserRegisterForm(data=data).is_valid())

        # try to register with confirmed password that does not match first password
        data = {'email': 'test@mail.ru', 'password': 'test', 'confirm_password': 'dont_match', 'proceed': 'register'}
        self.assertTrue(UserRegisterForm(data=data).is_valid())
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('passwords_dont_match'))

        # try to register with invalid email
        data = {'email': 'test', 'password': 'test', 'confirm_password': 'test', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('invalid_email'))

        # try to register with already used email
        data = {'email': self.existing_user.email, 'password': 'bla', 'confirm_password': 'bla', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertTemplateUsed(response=response, template_name='app/register.html')
        self.assertTrue(response.context.get('user_already_exist'))

        # check if activation link was sent by e-email
        data = {'email': 'test@mail.ru', 'password': 'test', 'confirm_password': 'test', 'proceed': 'register'}
        response = self.c.post('/app/register', data=data, follow=True, secure=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate your DjangoGramm account.')
        self.assertTemplateUsed(response=response, template_name='app/acc_active_email.html')
        self.assertTemplateUsed(response=response, template_name='app/activation_link_sent.html')




