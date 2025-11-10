from django.template.defaulttags import register

@register.filter
def get_item(dictionary, key):
    """Permite obtener un valor de un diccionario usando una variable como llave en el template"""
    return dictionary.get(key)