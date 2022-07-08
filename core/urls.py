from django.urls import path
from django.views.generic import TemplateView

from .views import HomeView, ItemDetailView

app_name = "core"


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("product/<slug>/", ItemDetailView.as_view(), name="product"),
    path(
        "data-protection/",
        TemplateView.as_view(template_name="data_protection.html"),
        name="data-protection",
    ),
    path(
        "impressum/",
        TemplateView.as_view(template_name="impressum.html"),
        name="impressum",
    ),
    path("api-doc/", TemplateView.as_view(template_name="api.html"), name="api-doc"),
]
