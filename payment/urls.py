from django.urls import path

from .views import PaypalView, capture, getClientId

app_name = "payment"

urlpatterns = [
    path("", PaypalView.as_view(), name="payment"),
    path("capture/<order_id>/", capture, name="paypal-capture"),
    path("client-id/", getClientId, name="client-id"),
]
