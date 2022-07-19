"""Viewsets for API Core"""

from rest_framework import viewsets, permissions
from core.api_core.serializers import ItemSerializer, CategorySerializer
from core.models import Item, CategoryItem


class IsAdminOrReadOnly(permissions.IsAdminUser):
    """Custom permission class, Admin can change else read only"""

    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or is_admin


class ItemViewSet(viewsets.ModelViewSet):
    """Item viewset, GET for everyone. UPDATE PATCH PUT DELETE only admin. Filter items.stock > 0"""

    queryset = Item.objects.order_by("-created_date").filter(stock__gt=0)
    serializer_class = ItemSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    """Category viewset, GET for everyone. UPDATE PATCH PUT DELETE only admin"""

    queryset = CategoryItem.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
