from django.db import models
from django.conf import settings
from django.utils import timezone
from menu.models import MenuItem  # assuming this is your MenuItem import
from accounts.models import User   # or wherever your User model is

class Stock(models.Model):
    """
    Current stock levels for menu items
    """
    menu_item = models.OneToOneField(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='stock'
    )
    quantity = models.PositiveIntegerField(default=0)

    UNIT_CHOICES = [
        ('pcs', 'Pieces (pcs)'),
        ('kg',  'Kilograms (kg)'),
        ('g',   'Grams (g)'),
        ('l',   'Litres (L)'),
        ('ml',  'Millilitres (ml)'),
        ('pack', 'Packs'),
        ('box',  'Boxes'),
        ('bottle', 'Bottles'),
        ('bag',   'Bags'),
        ('other', 'Other (specify)'),
    ]

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='pcs',
        help_text="Unit of measurement for this stock item"
    )

    # Optional free-text fallback when unit = 'other'
    custom_unit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Specify custom unit if 'Other' is selected"
    )

    reorder_level = models.PositiveIntegerField(
        default=5,
        help_text="Alert when stock reaches this level"
    )

    # Added field for notes (as requested)
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or comments"
    )

    last_restocked = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['menu_item__name']

    def __str__(self):
        unit_display = dict(self.UNIT_CHOICES).get(self.unit, self.custom_unit or self.unit)
        return f"{self.menu_item.name} - {self.quantity} {unit_display}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def display_unit(self):
        """Helper to show correct unit in templates/admin"""
        if self.unit == 'other' and self.custom_unit:
            return self.custom_unit
        return dict(self.UNIT_CHOICES).get(self.unit, self.unit)

    def add_stock(self, quantity, user, notes=""):
        """Add stock and create transaction record"""
        self.quantity += quantity
        self.last_restocked = timezone.now()
        self.save()

        StockTransaction.objects.create(
            stock=self,
            transaction_type='IN',
            quantity=quantity,
            balance_after=self.quantity,
            user=user,
            notes=notes
        )

    def remove_stock(self, quantity, user, notes=""):
        """Remove stock and create transaction record"""
        if self.quantity < quantity:
            raise ValueError(f"Not enough stock to remove {quantity} from {self.menu_item.name}")

        self.quantity -= quantity
        self.save()

        StockTransaction.objects.create(
            stock=self,
            transaction_type='OUT',
            quantity=quantity,
            balance_after=self.quantity,
            user=user,
            notes=notes
        )
class StockTransaction(models.Model):
    """
    History of all stock movements
    """
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('SALE', 'Sale'),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    balance_after = models.IntegerField(help_text="Stock balance after transaction")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.stock.menu_item.name} - {self.get_transaction_type_display()} ({self.quantity})"


class StockAlert(models.Model):
    """
    Low stock alerts for superadmin
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Resolved" if self.is_resolved else "Active"
        return f"{self.stock.menu_item.name} - {status}"