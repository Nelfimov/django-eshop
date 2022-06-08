from django.contrib import admin

from .models import Carousel, CategoryItem, Item, ItemImage


class ItemImageAdmin(admin.TabularInline):
    model = ItemImage
    extra = 3


class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'title', 'price', 'delivery_price',
        'discount', 'stock', 'ordered_counter',
    ]
    list_filter = [
        'category',
    ]
    inlines = [ItemImageAdmin]


class CarouselAdmin(admin.ModelAdmin):
    list_display = [
        'index', 'title',
    ]


admin.site.register(Item, ItemAdmin)
admin.site.register(CategoryItem)
admin.site.register(Carousel, CarouselAdmin)
