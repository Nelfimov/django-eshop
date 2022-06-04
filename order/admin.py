from django.contrib import admin

from .models import Order, Address, TrackingCompany, Refund


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'payment',
        'ordered',
        'being_delivered',
        'refund_requested',
        'refund_granted',
        'shipping_address',
        'billing_address',
    ]
    list_filter = [
        'ordered',
        'being_delivered',
        'refund_requested',
        'refund_granted'
    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payment'
    ]
    search_fields = ['user__username', 'ref_code']
    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'email',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(TrackingCompany)
admin.site.register(Refund)
