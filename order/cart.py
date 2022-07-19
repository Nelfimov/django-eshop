from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from core.models import Item
from .models import Order, OrderItem


def add_to_cart(request, slug):
    """
    Add item to order. If order does not exist, create new one.
    If user is authenticated, order.user will be filled.
    If user is anon, order.session_key will be used
    """
    item = get_object_or_404(Item, slug=slug)
    if item.stock <= 0:
        messages.warning(request, _("Unfortunately we do not have item on stock"))
        return redirect("core:product", slug=slug)
    if not request.user.is_authenticated and not request.session.exists(
        request.session.session_key
    ):
        request.session.create()
    order = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    ).first()
    if order is not None:
        order_item, created = OrderItem.objects.get_or_create(item=item, order=order)
        if not created:
            order_item.quantity += 1
            if order_item.quantity > item.stock:
                messages.warning(
                    request,
                    _("Unfortunately we do not have this " + "quantity on stock"),
                )
                return redirect("order:cart-summary")

            order_item.save()
            messages.info(request, _("Quantity was updated"))
            return redirect("order:cart-summary")
        messages.info(request, _("Quantity was updated"))
        return redirect("order:cart-summary")

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        start_date=timezone.now(),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    )
    order_item = OrderItem.objects.create(item=item, order=order)
    messages.info(request, _("Quantity was updated"))
    return redirect("order:cart-summary")


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = (
        Order.objects.filter(
            ordered=False,
            user=(request.user if request.user.is_authenticated else None),
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        .prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.filter(item=item))
        )
        .first()
    )
    if order is not None:
        order_item = order.orderitem_set.first()

        if order_item is not None:
            order_item.delete()
            messages.info(request, _("This item was removed from your cart"))
            return redirect("order:cart-summary")

        messages.warning(request, _("This item was not in your cart"))
        return redirect("core:product", slug=slug)

    messages.warning(request, _("Your cart is empty"))
    return redirect("core:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = (
        Order.objects.filter(
            ordered=False,
            user=(request.user if request.user.is_authenticated else None),
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        .prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.filter(item=item))
        )
        .first()
    )
    if order is not None:
        order_item = order.orderitem_set.all().first()
        if order_item is not None:
            if order_item.quantity <= 1:
                order_item.delete()
            else:
                order_item.quantity -= 1
                order_item.save()
            messages.info(request, _("This item quantity was updated"))
            return redirect("order:cart-summary")

        messages.info(request, _("This item was not in your cart"))
        return redirect("core:product", slug=slug)

    messages.info(request, _("You do not have an active cart"))
    return redirect("core:product", slug=slug)
