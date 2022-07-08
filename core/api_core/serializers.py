from core.models import Item, CategoryItem
from rest_framework import serializers


class ItemSerializer(serializers.HyperlinkedModelSerializer):
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


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CategoryItem
        fields = [
            "name",
            "slug",
        ]
