from math import perm
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import authentication, permissions
from core.api_core.serializers import ItemSerializer

from core.models import Item
from order.api_order.serializers import OrderSerializer
from order.models import Order, OrderItem


@api_view(["GET"])
def add_to_cart(request, slug):
    """
    Add item to order. If order does not exist, create new one.
    If user is authenticated, order.user will be filled.
    If user is anon, order.session_key will be used
    """
    item = get_object_or_404(Item, slug=slug)
    if item.stock <= 0:
        return Response({"error": "Item out of stock"})
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
        order_serializer = OrderSerializer(order)
        order_item, created = OrderItem.objects.get_or_create(item=item, order=order)
        if not created:
            order_item.quantity += 1
            if order_item.quantity > item.stock:
                return Response({"error": "Order quantity exceeds item stock"})
            order_item.save()
            return Response(order_serializer.data)
        return Response(order_serializer.data)

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
