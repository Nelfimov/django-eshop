from rest_framework import serializers

from ..models import Item


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Item
        fields = [
            "title",
            "price",
            "delivery_price",
            "discount",
            "category",
            "stock",
            "description",
            "created_date",
        ]
