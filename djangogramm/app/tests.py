from django.test import TestCase, Client

from .models import User
from .views import Authentication, UserEnterInfoView, Feed
from .forms import UserLoginForm


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


