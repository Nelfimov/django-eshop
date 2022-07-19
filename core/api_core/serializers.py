from rest_framework import serializers
from core.models import Item, CategoryItem


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    """Item serializer"""

    class Meta:
        model = Item
        fields = [
            "slug",
            "title",
            "price",
            "delivery_price",
            "discount",
            "category",
            "stock",
            "description",
            "created_date",
        ]
        extra_kwargs = {
            "title": {"required": True},
            "price": {"required": True},
            "delivery_price": {"required": True},
            "discount": {"required": True},
            "stock": {"required": True},
            "description": {"required": True},
        }


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    """Category serializer"""

    class Meta:
        model = CategoryItem
        fields = [
            "name",
            "slug",
        ]
