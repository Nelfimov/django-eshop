from django.contrib import admin

from .models import Item, Order, OrderItem, Refund, Address, UserProfile
from payment.models import Payment


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment', 'ordered', 'being_delivered', 'received', 'refund_requested', 'refund_granted', 'shipping_address']
    list_filter = ['ordered', 'being_delivered', 'received', 'refund_requested', 'refund_granted']
    list_display_links = ['user', 'shipping_address', 'payment']
    search_fields = ['user__username', 'ref_code']


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)
