# Generated by Django 3.2.4 on 2022-01-15 10:08

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_auto_20220115_1458'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.CheckConstraint(check=models.Q(('followee', django.db.models.expressions.F('follower')), _negated=True), name='followee_and_follower_cannot_be_equal'),
        ),
    ]
