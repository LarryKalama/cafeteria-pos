from django.contrib import admin
from .models import Category, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['order', 'name']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'selling_price', 'track_inventory',
                    'is_available', 'is_active']
    list_filter = ['category', 'is_available', 'is_active', 'track_inventory']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'is_active']
    ordering = ['category', 'name']
