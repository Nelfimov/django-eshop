from django.urls import path

from .views import CheckoutView


app_name = "checkout"


urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
]
