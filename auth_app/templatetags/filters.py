from django import template
from django.forms.boundfield import BoundField
from django.utils.safestring import SafeString

register = template.Library()

@register.filter
def replace(value: str, arg: str) -> str:
    original_string, replacement_string = arg.split(',')
    return value.replace(original_string, replacement_string)


@register.filter
def add_class(field: BoundField, css_class: str) -> SafeString:
    """フォームフィールドのウィジェットにCSSクラスを追加して描画する。"""
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get('class', '')
    attrs['class'] = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs=attrs)
