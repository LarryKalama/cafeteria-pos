from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    """
    Menu Categories: Hot Drinks, Cold Drinks, Snacks, Main Dishes
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """
    Individual menu items with pricing and stock tracking
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Selling Price (KSH)"
    )
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    # Stock tracking
    track_inventory = models.BooleanField(
        default=True, 
        help_text="Enable inventory tracking for this item"
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        status = "✓ Available" if self.is_available else "✗ Unavailable"
        return f"{self.name} - KSh {self.selling_price:.0f} ({status})"
    
    @property
    def current_stock(self):
        """Get current stock level from inventory"""
        if not self.track_inventory:
            return None
        try:
            from inventory.models import Stock
            stock = Stock.objects.get(menu_item=self)
            return stock.quantity
        except:
            return 0
    
    @property
    def is_low_stock(self):
        """Check if stock is below threshold"""
        from django.conf import settings
        if not self.track_inventory:
            return False
        current = self.current_stock
        return current is not None and current <= settings.LOW_STOCK_THRESHOLD
    
    @property
    def stock_status(self):
        """Get stock status for display"""
        if not self.track_inventory:
            return "No tracking"
        if not self.is_available:
            return "Out of stock"
        if self.is_low_stock:
            return f"Low ({self.current_stock})"
        return f"In stock ({self.current_stock})"