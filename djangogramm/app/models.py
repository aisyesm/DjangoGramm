from django.db import models as db_models
from django.contrib.auth import models as auth_models


class User(auth_models.User):
    bio = db_models.TextField(blank=True)
    avatar = db_models.ImageField(null=True)


class Post(db_models.Model):
    user = db_models.ForeignKey(User, on_delete=db_models.CASCADE)
    image = db_models.ImageField()
    caption = db_models.CharField(max_length=200, blank=True)
    pub_date = db_models.DateTimeField('date posted')
