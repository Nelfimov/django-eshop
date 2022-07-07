from django.contrib import admin

from .models import Address


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "email",
        "shipping_name",
        "shipping_street_address",
        "shipping_apartment_address",
        "shipping_country",
        "default",
    ]
    list_display_links = ["email", "user", "shipping_name"]
    list_filter = ["user", "default", "shipping_country"]
    search_fields = ["user", "email", "shipping_country"]


admin.site.register(Address, AddressAdmin)
