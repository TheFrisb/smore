from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe, SafeString

register = template.Library()


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

    sprite_path: str = static("assets/svg/sprite.svg")
    svg_markup: str = (
        f'<svg class="{css_classes or ""}"><use xlink:href="{sprite_path}#{icon_name}"></use></svg>'
    )
    return mark_safe(svg_markup)
