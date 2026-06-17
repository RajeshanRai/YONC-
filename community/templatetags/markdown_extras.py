import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)')

@register.filter
def markdown_links(value):
    """Convert simple Markdown [text](url) links into HTML anchors.
    This intentionally supports only absolute http/https links to avoid accidental conversions.
    """
    if not value:
        return ''
    def repl(m):
        text = m.group(1)
        url = m.group(2)
        return f'<a href="{url}">{text}</a>'
    out = MD_LINK_RE.sub(repl, value)
    return mark_safe(out)
