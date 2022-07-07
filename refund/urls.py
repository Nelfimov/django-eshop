from django.urls import path

from .views import RequestRefundView


app_name = "refund"


urlpatterns = [
    path("request-refund/", RequestRefundView.as_view(), name="request-refund"),
]
