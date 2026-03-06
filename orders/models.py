from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from menu.models import MenuItem

class Order(models.Model):
    """
    Customer orders
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_KITCHEN', 'In Kitchen'),
        ('READY', 'Ready'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='orders_served'
    )
    customer_name = models.CharField(max_length=100, blank=True)
    table_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name or 'Walk-in'}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-YYYYMMDD-XXX
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(
                order_number__startswith=f'ORD-{date_str}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.order_number = f'ORD-{date_str}-{new_num:03d}'
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate order totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        self.tax = 0  # Add tax calculation if needed
        self.total = self.subtotal + self.tax
        self.save()
    
    def mark_completed(self):
        """Mark order as completed"""
        from django.utils import timezone
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Deduct stock for items with inventory tracking
        for item in self.items.all():
            if item.menu_item.track_inventory:
                try:
                    stock = item.menu_item.stock
                    stock.remove_stock(
                        quantity=item.quantity,
                        user=self.waiter,
                        notes=f"Order #{self.order_number}"
                    )
                    
                    # Update menu item availability if out of stock
                    if stock.is_out_of_stock:
                        item.menu_item.is_available = False
                        item.menu_item.save()
                except:
                    pass


class OrderItem(models.Model):
    """
    Individual items in an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, help_text="Special instructions")
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total
        self.total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order totals
        self.order.calculate_totals()