from django.contrib import admin

from .models import Cart, CartItem


class CartAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'creation_date',
        'checked_out',
        'session_key',
    ]
    list_filter = [
        'user',
        'checked_out'
    ]
    list_display_links = [
        'user',
        'session_key',
    ]


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
