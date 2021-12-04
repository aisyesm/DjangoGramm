from django.db import models
from django.conf import settings
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email))

        user.set_password(password)
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
    first_name = models.TextField(blank=True)
    last_name = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(null=True, blank=True, upload_to=user_avatar_path)

    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_posts_path, height_field=None, width_field=None)
    caption = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date posted', auto_now=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return f"{self.pub_date} {self.user}; caption: {self.caption}"
