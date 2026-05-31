from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def translate_criterion(criterion):
    """Переводит название критерия на русский"""
    translations = {
        'price': 'Цена',
        'distance': 'Расстояние',
        'experience': 'Опыт',
        'rating': 'Рейтинг',
        'education': 'Образование',
        'PRICE': 'Цена',
        'DISTANCE': 'Расстояние',
        'EXPERIENCE': 'Опыт',
        'RATING': 'Рейтинг',
        'EDUCATION': 'Образование',
    }
    return translations.get(criterion, criterion.capitalize())