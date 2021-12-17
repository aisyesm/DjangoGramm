"""Helper functions."""

from datetime import datetime

import pytz


def get_timedelta_for_post(pub_date: datetime) -> str:
    """Returns Instagram like post time from datetime object."""
    now = datetime.now(pytz.timezone('Asia/Oral'))
    diff = now - pub_date
    res = 'undefined'  # in case something goes wrong
    if diff.days == 0:
        if diff.seconds >= 3600:
            hours_ago = diff.seconds // 3600
            res = f"{hours_ago} hour ago" if hours_ago == 1 else f"{hours_ago} hours ago"
        elif 60 <= diff.seconds < 3600:
            min_ago = diff.seconds // 60
            res = f"{min_ago} minute ago" if min_ago == 1 else f"{min_ago} minutes ago"
        elif diff.seconds < 60:
            res = f"seconds ago" if diff.seconds < 10 else f"{diff.seconds} seconds ago"
    elif 1 <= diff.days <= 6:
        res = f'{diff.days} day ago' if diff.days == 1 else f'{diff.days} days ago'
    elif diff.days == 7:
        res = f'1 week ago'
    elif diff.days > 7:
        day_of_month = pub_date.strftime('%d').lstrip('0')
        month = pub_date.strftime('%B')
        year = pub_date.strftime('%Y')
        res = f"{month} {day_of_month}" if diff.days < 365 else f"{month} {day_of_month}, {year}"
    res = res.upper()
    return res
