from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})


@register.filter(name='highlight')
def highlight(text, search):
    """検索キーワードをハイライト表示するフィルター"""
    if not search:
        return text
    
    # HTMLエスケープを考慮してハイライト
    highlighted = re.sub(
        f'({re.escape(search)})', 
        r'<mark>\1</mark>', 
        str(text), 
        flags=re.IGNORECASE
    )
    return mark_safe(highlighted)
