# Generated by Django 3.2.4 on 2022-01-15 09:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_user_following'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together={('followee', 'follower')},
        ),
    ]
