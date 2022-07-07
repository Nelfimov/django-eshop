from django.contrib import admin

from .models import Refund


class RefundAdminInline(admin.TabularInline):
    model = Refund
    max_num = 0
    readonly_fields = [
        "order",
        "reason",
        "image",
    ]
    can_delete = False


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


admin.site.register(Refund, RefundAdmin)
