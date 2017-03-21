from django import template

register = template.Library()


@register.filter
def join(lst, sep):
    """Joins a list with the specified separator."""
    return sep.join([str(elem) for elem in lst])
