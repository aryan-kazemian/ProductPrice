from django.contrib import admin
from .models import Product, PriceRecord, PriceChangeLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'barcode',
        'name',
        'on_pack',
        'sale_price',
        'off_price',
        'flag',
        'updated_at',
    )
    search_fields = ('barcode', 'name')
    list_filter = ('on_pack', 'flag')
    ordering = ('name',)


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'price')
    search_fields = ('product',)
    ordering = ('product',)


@admin.register(PriceChangeLog)
class PriceChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'old_price',
        'new_price',
        'changed_at',
    )
    search_fields = ('product__name', 'product__barcode')
    list_filter = ('changed_at',)
    ordering = ('-changed_at',)
