import os
import re
import shutil
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, Client
from django.core import mail
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By

from .models import User
from .views import Authentication, UserEnterInfoView, Feed, Register, UserProfile
from .forms import UserLoginForm, UserRegisterForm, UserFullInfoForm


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


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.c = Client()

    def test_logout(self):
        """Log user out and redirect to home page."""
        user = User.objects.create_user(email='test', password='test', is_active=True,
                                        first_name='test', last_name='test')
        self.c.login(email=user.email, password='test')
        response = self.c.get('/app/logout', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')


class UserEnterInfoTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(email='test@mail.com', password='test', is_active=True)

    def test_access_logged_in_only(self):
        """Only logged-in users can access the view."""
        response = self.c.get(f'/app/{self.user.pk}/enter_info', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')

    def test_user_has_to_provide_first_and_last_names(self):
        """Form cannot be submitted when first and last names are not provided."""
        self.c.login(email=self.user.email, password='test')
        data = {'proceed': 'continue'}
        self.assertFalse(UserFullInfoForm(data=data).is_valid())
        data['first_name'] = 'Test'
        self.assertFalse(UserFullInfoForm(data=data).is_valid())
        data['last_name'] = 'Test'
        self.assertTrue(UserFullInfoForm(data=data).is_valid())

    def test_enter_info_and_redirect(self):
        """Make sure provided data was uploaded and added to user.
        Then redirect to profile page."""
        self.c.login(email=self.user.email, password='test')
        with open('/Users/ais/Desktop/test.jpg', 'rb') as img:
            data = {'first_name': 'Test', 'last_name': 'Test', 'bio': 'some bio for test', 'avatar': img}
            response = self.c.post(f'/app/{self.user.pk}/enter_info', data=data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.resolver_match.func.__name__, UserProfile.as_view().__name__)
            self.assertTemplateUsed(response=response, template_name='app/user_detail.html')
            user = User.objects.filter(email=self.user.email).first()
            self.assertEqual(user.first_name, 'Test')
            self.assertEqual(user.last_name, 'Test')
            self.assertEqual(user.bio, 'some bio for test')
            self.assertIsNotNone(user.avatar)
            pattern = r'(\d+)/avatar/(\S+)'
            avatar_path = re.search(pattern, str(user.avatar))
            self.assertIsNotNone(avatar_path)
            user_id, file_name = avatar_path.group(1), avatar_path.group(2)
            self.assertEqual(file_name, 'test.jpg')
            for folder in os.listdir(settings.MEDIA_ROOT):
                if folder == user_id:
                    shutil.rmtree(f'{settings.MEDIA_ROOT}/{folder}')


class UserEditInfoTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        with open('/Users/ais/Desktop/test.jpg', 'rb') as img:
            self.user = User.objects.create_user(email='test@mail.com', password='test', is_active=True,
                                                 first_name='Test', last_name='Test', bio='Test', avatar=img)

    def test_access_logged_in_only(self):
        """Only logged-in users can access the view."""
        response = self.c.get(f'/app/{self.user.pk}/edit_profile', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')

    def test_user_has_to_provide_first_and_last_names(self):
        """Form cannot be submitted when first and last names are not provided."""
        self.c.login(email=self.user.email, password='test')
        data = {'proceed': 'continue'}
        response = self.c.post(f'/app/{self.user.pk}/edit_profile', data=data, follow=True)
        self.assertTemplateUsed(response=response, template_name='app/user_edit_profile.html')
        data['first_name'] = 'New'
        data['last_name'] = 'New'
        response = self.c.post(f'/app/{self.user.pk}/edit_profile', data=data, follow=True)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')


class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Chrome()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_cancel_returns_to_profile_page(self):
        """When pressing Cancel button, user returns to his profile page."""
        user = User.objects.create_user(email='test@gmail.com', password='test', is_active=True,
                                        first_name='Test', last_name='Test')
        self.selenium.get(f'{self.live_server_url}/app/')
        self.selenium.find_element(By.ID, value='id_email').send_keys(user.email)
        self.selenium.find_element(By.ID, value='id_password').send_keys('test')
        self.selenium.find_element(By.NAME, value='proceed').click()
        self.selenium.find_element(By.XPATH, value="//a[text()='My profile']").click()
        self.selenium.find_element(By.CLASS_NAME, value='edit_button').click()
        self.selenium.find_element(By.XPATH, value="//button[text()='Cancel']").click()
        self.assertEqual(self.selenium.current_url, f'{self.live_server_url}/app/{user.pk}/profile')


