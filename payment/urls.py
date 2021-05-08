from django.urls import path, include
from .views import StripeView, capture, getClientId, PaypalView

app_name = 'payment'

urlpatterns = [
    path('paypal/', PaypalView.as_view(), name='paypal'),
    path('paypal/capture/<order_id>/', capture, name='paypal-capture'),
    path('paypal/client-id/', getClientId, name='client-id'),
    path('stripe/', StripeView.as_view(), name='stripe')
]