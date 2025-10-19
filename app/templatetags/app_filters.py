from django import template
import re
from django.utils.safestring import mark_safe
from decimal import Decimal

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


@register.filter(name='comma_format')
def comma_format(value):
    """数値を三桁区切りでフォーマットするフィルター"""
    if value is None:
        return '0'
    
    try:
        # まず数値型に変換
        if isinstance(value, str):
            # 文字列の場合
            if '.' in value:
                num_value = float(value)
            else:
                num_value = int(value)
        elif isinstance(value, Decimal):
            # Decimal型の場合、floatに変換してから整数化
            num_value = float(value)
        elif isinstance(value, (int, float)):
            num_value = value
        else:
            # その他の型はそのまま返す
            return str(value)
        
        # 整数部分のみを取り出して三桁区切り
        int_value = int(num_value)
        return '{:,}'.format(int_value)
    except (ValueError, TypeError, AttributeError) as e:
        # エラーが発生した場合は元の値を返す
        return str(value)
