from django.contrib import admin
from .models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'paypal_id',
        'amount',
        'timestamp',
    ]
    list_display_links = [
        'user',
        'paypal_id',
        'amount',
    ]


admin.site.register(Payment, PaymentAdmin)
