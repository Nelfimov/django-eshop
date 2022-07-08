from rest_framework import viewsets, permissions
from core.api_core.serializers import ItemSerializer, CategorySerializer
from core.models import Item, CategoryItem


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.order_by("-created_date").filter(stock__gt=0)
    serializer_class = ItemSerializer
    permission_classes = [
        permissions.IsAdminUser,
        permissions.IsAuthenticatedOrReadOnly,
    ]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CategoryItem.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
