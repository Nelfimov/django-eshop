from django import template
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
