from django.urls import path, include
from .views import StripeView, capture, getClientId, PaypalView

app_name = 'payment'

urlpatterns = [
    path('paypal/', PaypalView.as_view(), name='pay'),
    # path('paypal/create/', create, name='paypal-create'),
    path('paypal/<order_id>/capture/', capture, name='paypal-capture'),
    path('paypal/client-id/', getClientId, name='client-id'),
    path('stripe/', StripeView.as_view(), name='stripe')
]
