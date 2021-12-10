from datetime import datetime
import pytz
from rest_framework import serializers
from .models import Post


class UserProfilePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'image']


class FeedPostSerializer(serializers.ModelSerializer):
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Post
        fields = ['image', 'caption', 'pub_date', 'user', 'user_avatar', 'user_email']

    def to_representation(self, instance):
        """Convert `pub_date` to time delta."""
        ret = super().to_representation(instance)
        pub_date = datetime.fromisoformat(ret['pub_date'])
        now = datetime.now(pytz.timezone('Asia/Oral'))
        diff = now - pub_date
        if diff.days == 0:
            if diff.seconds >= 3600:
                hours_ago = diff.seconds // 3600
                ret['pub_date'] = f"{hours_ago} hour ago" if hours_ago == 1 else f"{hours_ago} hours ago"
            elif 60 <= diff.seconds < 3600:
                min_ago = diff.seconds // 60
                ret['pub_date'] = f"{min_ago} minute ago" if min_ago == 1 else f"{min_ago} minutes ago"
            elif diff.seconds < 60:
                ret['pub_date'] = f"seconds ago" if diff.seconds < 10 else f"{diff.seconds} seconds ago"
        elif 1 <= diff.days <= 6:
            ret['pub_date'] = f'{diff.days} day ago' if diff.days == 1 else f'{diff.days} days ago'
        elif diff.days == 7:
            ret['pub_date'] = f'1 week ago'
        elif diff.days > 7:
            day_of_month = pub_date.strftime('%d').lstrip('0')
            month = pub_date.strftime('%B')
            year = pub_date.strftime('%Y')
            ret['pub_date'] = f"{month} {day_of_month}" if diff.days < 365 else f"{month} {day_of_month}, {year}"
        return ret
