from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Count
from django.views.decorators.cache import cache_page
from order.models import Order

register = template.Library()


@register.filter
def order_item_count(request):
    try:
        counter = (
            Order.objects.filter(
                ordered=False,
                user=(request.user if request.user.is_authenticated else None),
                session_key=(
                    None
                    if request.user.is_authenticated
                    else request.session.session_key
                ),
            )
            .annotate(Count("orderitem"))
            .first()
            .orderitem__count
        )
        return counter
    except:
        return 0


@cache_page(60 * 60)
@register.filter
def my_site_name(request):
    return get_current_site(request).name
