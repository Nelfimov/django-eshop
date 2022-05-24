from django.urls import path

from .views import (CartView, add_to_cart, remove_from_cart,
                    remove_single_item_from_cart)

app_name = 'cart'


urlpatterns = [
    path('', CartView.as_view(), name='cart-summary'),
    path('add/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
]
