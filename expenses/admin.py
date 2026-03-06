from django.contrib import admin
from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('display_category', 'amount', 'date', 'paid_by', 'created_at')
    list_filter = ('date', 'category', 'paid_by')
    search_fields = ('custom_category', 'description', 'paid_by__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')