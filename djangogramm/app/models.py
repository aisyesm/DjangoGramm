import os

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.urls import reverse
from PIL import Image
from cloudinary.models import CloudinaryField as BaseCloudinaryField

EMPTY_USER_IMAGE = os.getenv('EMPTY_USER_IMAGE')


class CloudinaryAvatarField(BaseCloudinaryField):
    def upload_options(self, instance):
        return {
            'folder': f"media/{instance.id}/avatar/",
            'public_id': f"avatar_{instance.id}",
        }

    def pre_save(self, model_instance, add):
        self.options.update(self.upload_options(model_instance))
        return super().pre_save(model_instance, add)


class CloudinaryPostField(BaseCloudinaryField):
    def upload_options(self, instance):
        print(instance.pub_date)
        return {
            'folder': f"media/{instance.user.id}/posts/",
            'public_id': f"{instance.user.id}_{instance.pub_date}",
        }

    def pre_save(self, model_instance, add):
        self.options.update(self.upload_options(model_instance))
        return super().pre_save(model_instance, add)


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email))

        user.set_password(password)
        if kwargs.get('is_active') is True:
            user.is_active = True
        if isinstance(kwargs.get('first_name'), str):
            user.first_name = kwargs.get('first_name')
        if isinstance(kwargs.get('last_name'), str):
            user.last_name = kwargs.get('last_name')
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


def user_avatar_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/avatar/<filename>
    return f'{instance.id}/avatar/{filename}'


def user_posts_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/posts/<filename>
    return f'{instance.user.id}/posts/{filename}'


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(blank=True, max_length=20)
    last_name = models.CharField(blank=True, max_length=20)
    bio = models.TextField(blank=True, max_length=70)
    avatar = CloudinaryAvatarField('image', default=EMPTY_USER_IMAGE, proxy='http://proxy.server:3128')
    followers = models.ManyToManyField('self', through='Subscription', through_fields=('followee', 'follower'))
    following = models.ManyToManyField('self', through='Subscription', through_fields=('follower', 'followee'))

    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    # code for Pillow, before using Cloudinary
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)  # saving image first
    #     if self.avatar:
    #         with Image.open(self.avatar.path) as img:
    #             if img.height > 512 or img.width > 512:
    #                 size = (512, 512)
    #                 img.thumbnail(size)
    #                 img.save(self.avatar.path, format="JPEG")  # saving image at the same path

    @property
    def is_staff(self):
        return self.is_admin


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    caption = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date posted', auto_now_add=True)
    likes = models.ManyToManyField(User, through='Like', related_name='users_liked')
    image = CloudinaryPostField('image', proxy='http://proxy.server:3128')

    class Meta:
        ordering = ['-pub_date']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.

    # def save(self):
    #     super().save()  # saving image first
    #     if self.image:
    #         with Image.open(self.image.path) as img:
    #             if img.height > 1024 or img.width > 1024:
    #                 size = (1024, 1024)
    #                 img.thumbnail(size)
    #                 img.save(self.image.path, format="JPEG")  # saving image at the same path

    def get_absolute_url(self):
        return reverse('app:post_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.id} {self.user}: (caption: {self.caption}, date: {self.pub_date})"


class Subscription(models.Model):
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_followees')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_followers')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['followee', 'follower'], name='unique_subscription'),
            models.CheckConstraint(check=~models.Q(followee=models.F('follower')),
                                   name='followee_and_follower_cannot_be_equal')
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.followee}, {self.follower})"

    def __str__(self):
        return f"{self.followee} is followed by {self.follower}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='only_one_like_from_user'),
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.post}, {self.user})"

    def __str__(self):
        return f"User {self.user.id} liked Post {self.post.id}"
