from django.urls import path

from .views import (CheckoutView, OrdersFinishedView, OrderView,
                    RequestRefundView, add_to_cart, remove_from_cart,
                    remove_single_item_from_cart)

app_name = 'order'


urlpatterns = [
    path('cart/', OrderView.as_view(), name='cart-summary'),
    path('cart/add/<slug>/', add_to_cart, name='add-to-cart'),
    path('cart/remove/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('cart/remove-single-item-from-cart/<slug>/',
         remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrdersFinishedView.as_view(), name='orders-finished'),
    path('request-refund/', RequestRefundView.as_view(),
         name='request-refund'),
]
