from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet d'accéder à un dict par clé dans les templates : {{ dict|get_item:key }}"""
    return dictionary.get(key)


@register.filter
def get_choice(question, letter):
    """Retourne le texte du choix A/B/C/D d'une question : {{ question|get_choice:'a' }}"""
    return getattr(question, f'choice_{letter}', '')
