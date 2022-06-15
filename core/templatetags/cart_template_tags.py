from django import template
from django.contrib.sites.shortcuts import get_current_site
from cart.models import Cart

register = template.Library()


@register.filter
def cart_item_count(request):
    if request.user.is_authenticated:
        qs = Cart.objects.filter(
            user=request.user,
            checked_out=False
        )
    else:
        qs = Cart.objects.filter(
            user=None,
            checked_out=False,
            session_key=request.session.session_key
        )
    if qs.exists():
        return qs[0].items.count()
    return 0


@register.filter
def my_site_name(request):
    return get_current_site(request).name
