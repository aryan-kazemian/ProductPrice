from django.contrib import admin
from .models import Product, PriceRecord, PriceChangeLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'barcode',
        'product_name',
        'on_pack',
        'sale_price',
        'off_price',
        'flag',
        'updated_at',
    )
    search_fields = ('barcode', 'product_name')
    list_filter = ('on_pack', 'flag')
    ordering = ('product_name',)


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'price')
    search_fields = ('barcode',)
    ordering = ('barcode',)


@admin.register(PriceChangeLog)
class PriceChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'old_price',
        'new_price',
        'changed_at',
    )
    search_fields = ('product__product_name', 'product__barcode')
    list_filter = ('changed_at',)
    ordering = ('-changed_at',)
