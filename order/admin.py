from django.contrib import admin
from django.utils.translation import gettext as _
from payment.models import Payment

from .models import Address, Order, OrderItem, Refund, TrackingCompany


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=True, refund_granted=True)
    short_description = _("Update orders to refund granted")


class OrderItemAdminInline(admin.TabularInline):
    model = OrderItem
    max_num = 0
    readonly_fields = [
        "item",
        "quantity",
    ]
    can_delete = False


class PaymentAdminInline(admin.TabularInline):
    model = Payment
    max_num = 0
    readonly_fields = ["paypal_id", "amount", "timestamp"]
    can_delete = False
    exclude = ["user"]


class RefundAdminInline(admin.TabularInline):
    model = Refund
    max_num = 0
    readonly_fields = [
        "order",
        "reason",
        "image",
    ]
    can_delete = False


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = [
        "ordered",
        "start_date",
        "user",
        "get_email",
        "session_key",
        "ordered_date",
        "ref_code",
        "shipping_address",
        "billing_address",
    ]
    list_display = [
        "ordered",
        "ref_code",
        "get_email",
        "shipping_address",
        "being_delivered",
        "refund_requested",
        "refund_granted",
    ]
    list_filter = [
        "ordered_date",
        "ordered",
        "being_delivered",
        "tracking_company",
        "refund_requested",
        "refund_granted",
    ]
    list_display_links = [
        "ref_code",
        "get_email",
        "shipping_address",
    ]
    search_fields = ["user__email", "ref_code"]
    actions = [make_refund_accepted]
    inlines = [
        OrderItemAdminInline,
        PaymentAdminInline,
        RefundAdminInline,
    ]

    @admin.display(description="Email")
    def get_email(self, obj):
        return obj.shipping_address.email


class AddressAdmin(admin.ModelAdmin):
    readonly_fields = [
        "user",
        "address_type",
        "default",
    ]
    list_display = [
        "user",
        "email",
        "street_address",
        "apartment_address",
        "country",
        "zip",
        "address_type",
        "default",
    ]
    list_filter = ["default", "address_type", "country"]
    search_fields = ["user", "street_address", "apartment_address", "zip"]


class RefundAdmin(admin.ModelAdmin):
    readonly_fields = [
        "order",
        "reason",
    ]
    list_display = [
        "order",
        "accepted",
    ]
    list_filter = ["accepted"]
    search_fields = ["order"]


admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(TrackingCompany)
admin.site.register(Refund, RefundAdmin)
