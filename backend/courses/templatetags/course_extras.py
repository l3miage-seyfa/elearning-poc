from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet d'accéder à un dict par clé dans les templates : {{ dict|get_item:key }}"""
    return dictionary.get(key)
