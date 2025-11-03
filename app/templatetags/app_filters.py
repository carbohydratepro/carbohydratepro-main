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


@register.filter(name='darker')
def darker(color, factor=0.7):
    """色を暗くするフィルター"""
    if not color:
        return color
    
    # #記号を除去
    color = color.lstrip('#')
    
    # 16進数カラーコードをRGBに変換
    try:
        if len(color) == 3:
            # 3桁の場合は6桁に変換 (#RGB -> #RRGGBB)
            color = ''.join([c*2 for c in color])
        
        if len(color) != 6:
            return f'#{color}'
        
        # RGBに分割
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # 各成分を暗くする
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        # 16進数に戻す
        return f'#{r:02x}{g:02x}{b:02x}'
    except (ValueError, TypeError):
        # エラーが発生した場合は元の色を返す
        return f'#{color}' if not color.startswith('#') else color
