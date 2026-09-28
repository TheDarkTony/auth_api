from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def auth_link(vn, label):
    try:
        signin_url = reverse(vn)
    except NoReverseMatch:
        return ''

    snippet = '<a href={href} >{lbl}</a>'
    snippet = format_html(snippet, href=signin_url, lbl=label)
    return mark_safe(snippet)