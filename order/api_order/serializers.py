from rest_framework import serializers
from order.models import Order, OrderItem


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    """Order serializer"""

    class Meta:
        model = Order
        fields = "__all__"


class OrderItemSerializer(serializers.HyperlinkedModelSerializer):
    """Order Item serializer"""

    class Meta:
        model = OrderItem
        fields = "__all__"
