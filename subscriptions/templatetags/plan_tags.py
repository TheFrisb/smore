from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def price_interval(price):
    """
    Display recurring interval like:
    - 'per week'
    - 'per month'
    - 'every 3 months'
    """
    if not price:
        return ""

    count = getattr(price, "interval_count", 1)
    interval = getattr(price, "interval", "").lower()

    if count == 1:
        return _("per %(interval)s") % {"interval": interval}
    return _("every %(count)d %(interval)s%(plural)s") % {
        "count": count,
        "interval": interval,
        "plural": "s" if count > 1 else "",
    }


@register.filter
def duration_label(price):
    """
    Display interval duration like:
    - 'One week'
    - 'One month'
    - 'Three months'
    """
    if not price:
        return ""

    count = getattr(price, "interval_count", 1)
    interval = getattr(price, "interval", "").lower()

    if count == 1:
        return _("One %(interval)s") % {"interval": interval}
    return _("%(count)s %(interval)s%(plural)s") % {
        "count": _("Three") if count == 3 else str(count),
        "interval": interval,
        "plural": "s" if count > 1 else "",
    }
