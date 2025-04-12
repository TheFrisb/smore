from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe, SafeString

register = template.Library()


@register.filter(name="multiply")
def multiply(value, arg):
    return value * arg


@register.filter(name="is_link_active")
def is_link_active(request, url_name):
    """
    Returns True if the current URL matches the given url_name, otherwise False.
    """

    return request.path == reverse(url_name)


@register.simple_tag
def svg_icon(icon_name: str = None, css_classes: str = None) -> SafeString:
    """
    Generates an SVG <use> tag to include an icon from the sprite.


    :param: icon_name (str): The ID of the icon in the sprite file (required).
    :param: css_classes (str): Optional Tailwind or custom classes for styling.


    :returns: SafeString: The generated SVG markup, marked safe for rendering as HTML.
    """
    if not icon_name:
        raise ValueError("The 'icon_name' parameter is required.")

    sprite_path: str = static("assets/svg/sprite13.svg")
    svg_markup: str = (
        f'<svg class="{css_classes or ""}"><use xlink:href="{sprite_path}#{icon_name}"></use></svg>'
    )
    return mark_safe(svg_markup)


@register.simple_tag
def get_full_url(url_name) -> str:
    """
    Returns the URL to redirect to after signing in with Google OAuth.
    """
    base_url = settings.BASE_URL
    view_url = reverse(url_name)

    return f"{base_url}{view_url}"


@register.simple_tag
def get_language_flag_icon_name(language_code: str) -> str:
    """
    Returns the SVG ID for the flag of the given language code.
    """
    flags = {
        "en": "enFlagIcon",
        "el": "elFlagIcon",
        "de": "deFlagIcon",
    }

    return flags.get(language_code.lower()[:2], "globalFlagIcon")


@register.filter(name="divide")
def divide(value, arg):
    # divide, to 2 decimal places
    return round(value / arg, 2)
