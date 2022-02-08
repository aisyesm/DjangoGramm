from datetime import datetime
from rest_framework import serializers
from .models import Post, Subscription, Like, User
from .helpers import get_timedelta_for_post


class UserProfilePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'image', 'likes']
        read_only_fields = ['id', 'image', 'likes']


class FeedPostSerializer(serializers.ModelSerializer):
    user_avatar = serializers.ImageField(source='user.avatar')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = Post
        fields = ['id', 'image', 'caption', 'pub_date', 'user', 'user_avatar', 'first_name', 'last_name', 'likes']
        read_only_fields = ['id', 'image', 'caption', 'pub_date', 'user', 'user_avatar', 'first_name', 'last_name', 'likes']

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


class LikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = '__all__'

    def validate(self, attrs):
        """Check if user wants to add existing like."""
        if Like.objects.filter(post=attrs['post'], user=attrs['user']):
            raise serializers.ValidationError('user cannot like post twice')
        return attrs


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']
        read_only_fields = ['first_name', 'last_name', 'avatar']
