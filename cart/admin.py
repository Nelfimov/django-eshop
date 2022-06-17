from sys import displayhook
from django.contrib import admin
from django.contrib.admin.decorators import display
from django.utils.translation import gettext as _

from .models import Cart, CartItem


class CartAdmin(admin.ModelAdmin):
    readonly_fields = [
        'user',
        'checked_out',
        'items',
        'session_key',
    ]
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


class CartItemAdmin(admin.ModelAdmin):
    readonly_fields = [
        'item',
        'quantity',
        'ordered',
    ]
    list_display = [
        'id',
        'item',
        'quantity',
        'get_price',
        'get_total_item_price'
    ]
    list_display_links = [
        'id', 'item',
    ]

    @display(ordering='item__get_final_price', description='Price')
    def get_price(self, obj):
        return obj.item.get_final_price()


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
