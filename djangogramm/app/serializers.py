from rest_framework import serializers
from .models import Post


class UserProfilePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'image']


class FeedPostSerializer(serializers.ModelSerializer):
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    year = serializers.IntegerField(source='pub_date.year')
    month = serializers.IntegerField(source='pub_date.month')
    day = serializers.IntegerField(source='pub_date.day')

    class Meta:
        model = Post
        fields = ['image', 'caption', 'pub_date', 'year', 'month', 'day', 'user', 'user_avatar', 'user_email']
