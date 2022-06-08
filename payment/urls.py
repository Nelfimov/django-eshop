from django.urls import path
from .views import capture, getClientId, PaypalView

app_name = 'payment'

urlpatterns = [
    path('paypal/', PaypalView.as_view(), name='paypal'),
    path('paypal/capture/<order_id>/', capture, name='paypal-capture'),
    path('paypal/client-id/', getClientId, name='client-id'),
]
