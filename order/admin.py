from django.contrib import admin
from django.utils.translation import gettext as _
from .models import Order, Address, TrackingCompany, Refund


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=True, refund_granted=True)


make_refund_accepted.short_description = _('Update orders to refund granted')


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = [
        'items',
        'cart',
        'user',
        'get_email',
        'ordered_date',
        'ref_code',
        'payment',
        'shipping_address',
        'billing_address',
    ]
    list_display = [
        'ref_code',
        'get_email',
        'payment',
        'ordered',
        'shipping_address',
        'being_delivered',
        'refund_requested',
        'refund_granted',
    ]
    list_filter = [
        'ordered_date',
        'ordered',
        'being_delivered',
        'tracking_company',
        'refund_requested',
        'refund_granted',
    ]
    list_display_links = [
        'ref_code',
        'get_email',
        'shipping_address',
        'payment'
    ]
    search_fields = ['user__email', 'ref_code']
    actions = [make_refund_accepted]

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.shipping_address.email


class AddressAdmin(admin.ModelAdmin):
    readonly_fields = [
        'user',
        'address_type',
        'default',
    ]
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
