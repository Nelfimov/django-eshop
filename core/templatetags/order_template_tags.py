from django import template
from django.contrib.sites.shortcuts import get_current_site
from order.models import Order, OrderItem

register = template.Library()


@register.filter
def order_item_count(request):
    order_qs = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    )
    if order_qs.exists():
        return OrderItem.objects.filter(order=order_qs[0]).count()
    return 0


@register.filter
def my_site_name(request):
    return get_current_site(request).name
