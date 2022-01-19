from datetime import datetime
from rest_framework import serializers
from .models import Post, Subscription, User
from .helpers import get_timedelta_for_post


class UserProfilePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'image']
        read_only_fields = ['id', 'image']


class FeedPostSerializer(serializers.ModelSerializer):
    user_avatar = serializers.ImageField(source='user.avatar')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = Post
        fields = ['image', 'caption', 'pub_date', 'user', 'user_avatar', 'first_name', 'last_name']
        read_only_fields = ['image', 'caption', 'pub_date', 'user', 'user_avatar', 'first_name', 'last_name']

    def to_representation(self, instance):
        """Convert `pub_date` to time delta."""
        ret = super().to_representation(instance)
        pub_date = datetime.fromisoformat(ret['pub_date'])
        ret['pub_date'] = get_timedelta_for_post(pub_date)
        return ret


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = '__all__'
