from django import template

register = template.Library()

@register.filter
def fix_float(value):
    """Заменяет запятую на точку для CSS"""
    if value is None:
        return '0'
    return str(value).replace(',', '.')

@register.filter
def get_item(dictionary, key):
    """Получение значения из словаря по ключу"""
    return dictionary.get(key, 0)

@register.filter
def subtract(value, arg):
    """Вычитание"""
    if isinstance(value, dict):
        return value.get(arg, 0)
    return value - arg