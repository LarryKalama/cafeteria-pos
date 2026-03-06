from django.contrib import admin
from .models import Stock, StockTransaction, StockAlert


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        'menu_item',
        'quantity',
        'unit',
        'reorder_level',
        'is_low_stock',        # custom method
        'last_restocked',      # correct field name
        'is_out_of_stock',     # custom method
    )
    list_filter = (
        'unit',
        'last_restocked',      # correct field name
        'quantity',
    )
    search_fields = ('menu_item__name',)
    readonly_fields = (
        'last_restocked',      # correct field name
        'quantity',
        'menu_item',
    )
    ordering = ('menu_item__name',)

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'transaction_type',
        'quantity',
        'balance_after',
        'user',
        'created_at',
    )
    list_filter = (
        'transaction_type',
        'created_at',
    )
    search_fields = (
        'stock__menu_item__name',
        'notes',
    )
    readonly_fields = (
        'created_at',
        'balance_after',
    )


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'message',
        'is_resolved',
        'created_at',
        'resolved_at',
    )
    list_filter = (
        'is_resolved',
        'created_at',
    )
    search_fields = (
        'stock__menu_item__name',
        'message',
    )
    readonly_fields = (
        'created_at',
        'resolved_at',
    )