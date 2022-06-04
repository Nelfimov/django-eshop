from django.urls import path

from .views import CheckoutView, OrderView, RequestRefundView

app_name = 'order'


urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderView.as_view(), name='orders-finished'),
    path('request-refund/', RequestRefundView.as_view(),
         name='request-refund'),
]
