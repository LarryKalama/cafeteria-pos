from django.contrib import admin
from .models import Payment, CreditCustomer, CreditSale, CreditPayment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'payment_method', 'amount', 'processed_by', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['order__order_number', 'mpesa_transaction_code']
    readonly_fields = ['created_at']

@admin.register(CreditCustomer)
class CreditCustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'total_credit', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone_number', 'email']
    readonly_fields = ['total_credit', 'created_at', 'updated_at']

class CreditPaymentInline(admin.TabularInline):
    model = CreditPayment
    extra = 0
    readonly_fields = ['created_at']

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'order', 'total_amount', 'amount_paid', 
                    'balance', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__name', 'order__order_number']
    readonly_fields = ['balance', 'created_at', 'updated_at']
    inlines = [CreditPaymentInline]
