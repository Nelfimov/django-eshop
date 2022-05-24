from django.urls import path
from django.views.generic import TemplateView

from .views import (CheckoutView, HomeView, ItemDetailView,
                    OrderView, RequestRefundView)

app_name = 'core'


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderView.as_view(), name='orders-finished'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('request-refund/', RequestRefundView.as_view(),
         name='request-refund'),
    path('data-protection/',
         TemplateView.as_view(template_name='data_protection.html'),
         name='data-protection'),
    path('impressum/',
         TemplateView.as_view(template_name='impressum.html'),
         name='impressum'),
]
