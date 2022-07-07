from django.contrib import admin
from django.utils.translation import gettext as _
from payment.models import Payment

from .models import Order, OrderItem, TrackingCompany
from refund.admin import RefundAdminInline


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


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = [
        "ordered",
        "start_date",
        "user",
        "get_email",
        "session_key",
        "ordered_date",
        "ref_code",
        "address",
    ]
    list_display = [
        "ordered",
        "ref_code",
        "get_email",
        "address",
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
        "address",
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
        if obj.address:
            return obj.address.email
        return "-"


admin.site.register(Order, OrderAdmin)
admin.site.register(TrackingCompany)
