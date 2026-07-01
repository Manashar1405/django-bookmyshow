from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def preserve_query_params(context, **kwargs):
    """
    Preserves existing GET parameters while allowing updates/additions.
    Usage: {% preserve_query_params page=2 sort='latest' %}
    """
    request = context.get('request')
    if not request:
        return ''

    # Get a mutable copy of the current GET parameters
    query_dict = request.GET.copy()

    for key, value in kwargs.items():
        if value is None:
            query_dict.pop(key, None)
        else:
            query_dict[key] = value

    return f"?{query_dict.urlencode()}"
