from django import template

register = template.Library()

@register.filter
def replace(value: str, arg: str) -> str:
    original_string, replacement_string = arg.split(',')
    return value.replace(original_string, replacement_string)
