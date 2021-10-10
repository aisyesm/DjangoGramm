from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(null=True)

    def __str__(self):
        return self.user.get_username()


class Post(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    image = models.ImageField()
    caption = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date posted')

    def __str__(self):
        return f"{self.account}: {self.caption[:20]}"
