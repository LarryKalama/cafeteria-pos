from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'waiter', 'customer_name', 'table_number', 
                    'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer_name']
    readonly_fields = ['order_number', 'subtotal', 'tax', 'total', 
                       'created_at', 'updated_at', 'completed_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'waiter', 'customer_name', 'table_number', 'status')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
