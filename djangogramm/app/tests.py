import os
import re
import shutil
import time
import unittest

from datetime import datetime, timedelta

import pytz
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, Client
from django.core import mail
from django.conf import settings
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .helpers import get_timedelta_for_post
from .models import User, Post, Subscription
from .views import Authentication, UserEnterInfoView, Feed, Register, UserProfile, PostDetail
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
        with open(f'{settings.MEDIA_ROOT}/test.jpg', 'rb') as img:
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
        with open(f'{settings.MEDIA_ROOT}/test.jpg', 'rb') as img:
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

    def test_user_can_edit_profile(self):
        """After submitting form user profile gets updated."""
        self.c.login(email=self.user.email, password='test')
        with open(f'{settings.MEDIA_ROOT}/test1.jpg', 'rb') as img:
            data = {'first_name': 'New', 'last_name': 'New', 'bio': 'New', 'avatar': img, 'proceed': 'continue'}
            response = self.c.post(f'/app/{self.user.pk}/edit_profile', data=data, follow=True)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')
        user = User.objects.filter(email=self.user.email).first()
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'New')
        self.assertEqual(user.bio, 'New')
        self.assertIsNotNone(user.avatar)
        pattern = r'(\d+)/avatar/(\S+)'
        avatar_path = re.search(pattern, str(user.avatar))
        self.assertIsNotNone(avatar_path)
        user_id, file_name = avatar_path.group(1), avatar_path.group(2)
        self.assertEqual(file_name, 'test1.jpg')
        for folder in os.listdir(settings.MEDIA_ROOT):
            if folder == user_id:
                shutil.rmtree(f'{settings.MEDIA_ROOT}/{folder}')

    def test_user_cannot_edit_other_user_avatar(self):
        """Authenticated user cannot edit other user's avatar."""
        logged_in_user = User.objects.create_user(email='logged@mail.com', password='logged', is_active=True,
                                                  first_name='Logged', last_name='Logged')
        self.c.login(email=logged_in_user.email, password='logged')
        with open(f'{settings.MEDIA_ROOT}/test1.jpg', 'rb') as img:
            data = {'avatar': img, 'submit': 'Update'}
            response = self.c.post(f'/app/{self.user.pk}/change_avatar', data=data, follow=True)
        self.assertEqual(response.status_code, 403)


class UserProfileTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user1 = User.objects.create_user(email='test1@mail.com', password='test1', is_active=True,
                                              first_name='Test1', last_name='Test1')
        self.user2 = User.objects.create_user(email='test2@mail.com', password='test2', is_active=True,
                                              first_name='Test2', last_name='Test2')

    def test_access_to_profile_logged_in_only(self):
        """Only logged-in users can access the view."""
        response = self.c.get(f'/app/{self.user1.pk}/profile', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')

    def test_user_can_control_only_own_profile(self):
        """User cannot see Add Post, Edit Profile on someone else's profile."""
        self.c.login(email=self.user1.email, password='test1')
        response = self.c.get(f'/app/{self.user1.pk}/profile', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, UserProfile.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')
        self.assertTrue(response.context.get('can_edit'))
        response = self.c.get(f'/app/{self.user2.pk}/profile', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')
        self.assertFalse(response.context.get('can_edit'))


class UserPostsTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(email='test@mail.com', password='test', is_active=True,
                                             first_name='Test', last_name='Test')

    def test_access_to_posts_logged_in_only(self):
        """Only logged-in users can access the post views."""
        response = self.c.get(f'/app/{self.user.pk}/add_post', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')
        response = self.c.get(f'/app/p/1', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, Authentication.as_view().__name__)
        self.assertTemplateUsed(response=response, template_name='app/login.html')
        response = self.c.get(f'/app/p/1/delete', follow=True)
        self.assertEqual(response.status_code, 404)
        response = self.c.get(f'/app/p/1/update', follow=True)
        self.assertEqual(response.status_code, 404)

    def test_user_can_add_and_view_post(self):
        """User can add post and see its detail view."""
        self.c.login(email=self.user.email, password='test')
        with open(f'{settings.MEDIA_ROOT}/test1.jpg', 'rb') as img:
            data = {'caption': 'Wow caption', 'image': img}
            response = self.c.post(f'/app/{self.user.pk}/add_post', data=data, follow=True)
        self.assertEqual(len(self.user.post_set.all()), 1)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')

        post = Post.objects.filter(caption='Wow caption').first()
        response = self.c.get(f"/app/p/{post.pk}", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, PostDetail.as_view().__name__)
        for folder in os.listdir(settings.MEDIA_ROOT):
            if folder == str(self.user.pk):
                shutil.rmtree(f'{settings.MEDIA_ROOT}/{folder}')

    def test_user_can_update_post(self):
        """User can change post caption."""
        self.c.login(email=self.user.email, password='test')
        with open(f'{settings.MEDIA_ROOT}/test1.jpg', 'rb') as img:
            data = {'caption': 'Wow caption', 'image': img}
            self.c.post(f'/app/{self.user.pk}/add_post', data=data, follow=True)
        self.assertEqual(len(self.user.post_set.all()), 1)
        post = Post.objects.filter(caption='Wow caption').first()
        response = self.c.post(f'/app/p/{post.pk}/update', {'caption': 'New caption'}, follow=True)
        self.assertTemplateUsed(response=response, template_name='app/post_detail.html')
        post = Post.objects.get(id=post.pk)
        self.assertEqual(post.caption, 'New caption')

        for folder in os.listdir(settings.MEDIA_ROOT):
            if folder == str(self.user.pk):
                shutil.rmtree(f'{settings.MEDIA_ROOT}/{folder}')

    def test_user_can_delete_post(self):
        """User can delete his post."""
        self.c.login(email=self.user.email, password='test')
        with open(f'{settings.MEDIA_ROOT}/test1.jpg', 'rb') as img:
            data = {'caption': 'Wow caption', 'image': img}
            self.c.post(f'/app/{self.user.pk}/add_post', data=data, follow=True)
        self.assertEqual(len(self.user.post_set.all()), 1)
        post = Post.objects.filter(caption='Wow caption').first()
        response = self.c.post(f'/app/p/{post.pk}/delete', follow=True)
        self.assertTemplateUsed(response=response, template_name='app/user_detail.html')
        self.assertEqual(len(self.user.post_set.all()), 0)
        for folder in os.listdir(settings.MEDIA_ROOT):
            if folder == str(self.user.pk):
                shutil.rmtree(f'{settings.MEDIA_ROOT}/{folder}')


class UserPostsAPITestCase(APITestCase):
    fixtures = ['users.json', 'posts.json', 'subscriptions.json']

    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_posts(self):
        """
        Ensure api and query params return correct json.
        """
        url = reverse('app:posts')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(id=69)
        self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        response = self.client.get(url + '?start=1&offset=2', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        response = self.client.get(url + '?user_id=62', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class SubscriptionAPITestCase(APITestCase):
    fixtures = ['users.json', 'posts.json', 'subscriptions.json']

    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_subscription(self):
        """
        Ensure api return correct json.
        """
        url = reverse('app:subscription', kwargs={'follower_id': 62, 'followee_id': 69})

        # test user has to be authenticated
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # test user has to be admin or subscription owner
        user = User.objects.get(email='test1@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='admin@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 4, 'followee': 69, 'follower': 62})

    def test_delete_subscription(self):
        """
        Test delete single subscription route.
        """
        url = reverse('app:subscription', kwargs={'follower_id': 69, 'followee_id': 62})

        # test user has to be authenticated
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # test user has to be admin or subscription owner
        user = User.objects.get(email='test2@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='test1@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subscription.objects.filter(followee=62, follower=69).first(), None)

    def test_get_subscriptions(self):
        """
        Ensure api return correct json.
        """
        url = reverse('app:subscription_list', kwargs={'follower_id': 116})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='admin@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_post_subscriptions(self):
        """
        Ensure api creates a new subscription.
        """
        url = reverse('app:subscription_list', kwargs={'follower_id': 93})
        response = self.client.post(url, data={'followee_id': 62})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='admin@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data={'followee_id': 62})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('followee'), 62)
        self.assertEqual(response.data.get('follower'), 93)
        self.assertEqual(len(Subscription.objects.filter(followee__id=62, follower__id=93)), 1)

        # ensure cannot subscribe twice
        response = self.client.post(url, data={'followee_id': 62})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # ensure cannot subscribe to himself
        response = self.client.post(url, data={'followee_id': 91})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # ensure users have to exist
        response = self.client.post(url, data={'followee_id': 91})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class LikeAPITestCase(APITestCase):
    fixtures = ['users.json', 'posts.json', 'likes.json']

    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_likes(self):
        """
        Ensure api return correct json.
        """
        url = reverse('app:likes', kwargs={'post_id': 113})

        # test user has to be authenticated
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='test1@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_post_like(self):
        """
        Ensure api creates a new object.
        """
        url = reverse('app:likes', kwargs={'post_id': 113})

        # test user has to be authenticated
        response = self.client.post(url, data={'user_id': 103})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user = User.objects.get(email='test1@mail.com')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data={'user_id': 103})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        # test user cannot like twice
        response = self.client.post(url, data={'user_id': 103})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        response = self.client.post(url, data={'user_id': 'f'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, data={'blabla': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HelperFuncTestCase(unittest.TestCase):
    """Unit test functions from helpers.py."""

    def test_get_timedelta_for_post(self):
        """get_timedelta_for_post returns correct publication date to show user."""
        now = datetime.now(pytz.timezone('Asia/Oral'))
        pub_date = now - timedelta(seconds=3)
        self.assertEqual(get_timedelta_for_post(pub_date), 'SECONDS AGO')
        pub_date = now - timedelta(seconds=30)
        self.assertEqual(get_timedelta_for_post(pub_date), '30 SECONDS AGO')
        pub_date = now - timedelta(seconds=60)
        self.assertEqual(get_timedelta_for_post(pub_date), '1 MINUTE AGO')
        pub_date = now - timedelta(seconds=360)
        self.assertEqual(get_timedelta_for_post(pub_date), '6 MINUTES AGO')
        pub_date = now - timedelta(seconds=3600)
        self.assertEqual(get_timedelta_for_post(pub_date), '1 HOUR AGO')
        pub_date = now - timedelta(seconds=7300)
        self.assertEqual(get_timedelta_for_post(pub_date), '2 HOURS AGO')
        pub_date = now - timedelta(days=1)
        self.assertEqual(get_timedelta_for_post(pub_date), '1 DAY AGO')
        pub_date = now - timedelta(days=3)
        self.assertEqual(get_timedelta_for_post(pub_date), '3 DAYS AGO')
        pub_date = now - timedelta(days=7)
        self.assertEqual(get_timedelta_for_post(pub_date), '1 WEEK AGO')
        pub_date = now - timedelta(days=10)
        self.assertEqual(get_timedelta_for_post(pub_date),
                         f"{pub_date.strftime('%B').upper()} {pub_date.strftime('%d').lstrip('0')}")
        pub_date = now - timedelta(days=700)
        self.assertEqual(get_timedelta_for_post(pub_date),
                         f"{pub_date.strftime('%B').upper()} {pub_date.strftime('%d').lstrip('0')}, {pub_date.year}")


class MySeleniumTests(StaticLiveServerTestCase):
    fixtures = ['users.json', 'posts.json', 'subscriptions.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Chrome(ChromeDriverManager().install())
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_cancel_returns_to_profile_page(self):
        """When pressing Cancel button, user returns to his profile page."""
        self.selenium.get(f'{self.live_server_url}/app/')
        self.selenium.find_element(By.ID, value='id_email').send_keys('test1@mail.com')
        self.selenium.find_element(By.ID, value='id_password').send_keys('test1')
        self.selenium.find_element(By.NAME, value='proceed').click()
        self.selenium.find_element(By.XPATH, value="//i[@class='far fa-user-circle']").click()
        self.selenium.find_element(By.XPATH, value="//a[text()='Edit profile']").click()
        self.selenium.find_element(By.XPATH, value="//button[@id='cancel-btn']").click()
        self.assertEqual(self.selenium.current_url, f'{self.live_server_url}/app/69/profile')

    def test_user_profile_posts_load_on_scroll(self):
        """
        Initially loads last 9 posts on user profile.
        Loads next 9 or remaining posts (if user has less than 9) on each scroll to the bottom.
        """
        self.selenium.get(f'{self.live_server_url}/app/')
        self.selenium.find_element(By.ID, value='id_email').send_keys('test1@mail.com')
        self.selenium.find_element(By.ID, value='id_password').send_keys('test1')
        self.selenium.find_element(By.NAME, value='proceed').click()
        self.selenium.find_element(By.XPATH, value="//i[@class='far fa-user-circle']").click()
        self.selenium.find_element(By.XPATH, value="//a[text()='Profile']").click()
        posts = self.selenium.find_elements(By.CLASS_NAME, value='post-area')
        self.assertEqual(len(posts), 9)
        self.selenium.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(5)  # wait for posts to load
        posts = self.selenium.find_elements(By.CLASS_NAME, value='post-area')
        self.assertEqual(len(posts), 11)

    def test_feed_posts_load_on_scroll(self):
        """
        Initially loads last 7 posts on feed.
        Loads next 7 or remaining posts (if less than 7 left) on each scroll to the bottom.
        """
        self.selenium.get(f'{self.live_server_url}/app/')
        self.selenium.find_element(By.ID, value='id_email').send_keys('test25@mail.com')
        self.selenium.find_element(By.ID, value='id_password').send_keys('test25')
        self.selenium.find_element(By.NAME, value='proceed').click()
        time.sleep(5)  # wait for posts to load
        posts = self.selenium.find_elements(By.CSS_SELECTOR, value='.posts .card')
        self.assertEqual(len(posts), 7)
        self.selenium.execute_script("window.scrollTo(0, document.body.scrollHeight - 807)")
        time.sleep(5)
        posts = self.selenium.find_elements(By.CSS_SELECTOR, value='.posts .card')
        self.assertEqual(len(posts), 13)

    def test_my_profile_link_redirects_to_logged_in_user(self):
        """Press My Profile from another user's profile."""
        self.selenium.get(f'{self.live_server_url}/app/')
        self.selenium.find_element(By.ID, value='id_email').send_keys('test1@mail.com')
        self.selenium.find_element(By.ID, value='id_password').send_keys('test1')
        self.selenium.find_element(By.NAME, value='proceed').click()
        self.selenium.get(f'{self.live_server_url}/app/104/profile')
        self.selenium.find_element(By.XPATH, value="//i[@class='far fa-user-circle']").click()
        self.selenium.find_element(By.XPATH, value="//a[text()='Profile']").click()
        self.assertEqual(self.selenium.current_url, f'{self.live_server_url}/app/69/profile')
