from django.urls import include, path
from rest_framework import routers
from core.api_core import views

router = routers.DefaultRouter()
router.register(r"items", views.ItemViewSet)
router.register(r"categories", views.CategoryViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
