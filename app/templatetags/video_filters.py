# yourapp/templatetags/video_filters.py
import re
from django import template

register = template.Library()

@register.filter
def get_youtube_id(url):
    """YouTube URL から動画IDを取得。無効な場合は None を返す"""
    if not url:
        return None
    youtube_regex = (
        r'(?:youtu\.be/|youtube\.com/(?:.*v=|.*\/|.*embed\/|.*shorts\/))([^\?\&\#]+)'
    )
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None
