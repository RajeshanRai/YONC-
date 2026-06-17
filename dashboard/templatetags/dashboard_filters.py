from django import template

register = template.Library()


@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage."""
    try:
        return min(100, int(int(value) / int(total) * 100))
    except (ValueError, ZeroDivisionError):
        return 0
