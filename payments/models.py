from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from orders.models import Order

class Payment(models.Model):
    """
    Payment records for orders
    """
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('MPESA', 'M-Pesa'),
        ('CREDIT', 'Credit'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # M-Pesa specific
    mpesa_transaction_code = models.CharField(max_length=50, blank=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    
    # Cash specific
    amount_tendered = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    change_given = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Credit specific
    credit_customer = models.ForeignKey(
        'CreditCustomer', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Metadata
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.get_payment_method_display()} - KSh {self.amount}"


class CreditCustomer(models.Model):
    """
    Customers who buy on credit
    """
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Credit info
    total_credit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Total outstanding credit"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    @property
    def pending_credit(self):
        """Calculate total pending credit"""
        return self.credit_sales.filter(
            status__in=['PENDING', 'PARTIAL']
        ).aggregate(
            total=models.Sum('balance')
        )['total'] or Decimal('0.00')
    
    def update_total_credit(self):
        """Update total credit amount"""
        self.total_credit = self.pending_credit
        self.save()


class CreditSale(models.Model):
    """
    Credit sales tracking
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    
    customer = models.ForeignKey(
        CreditCustomer, 
        on_delete=models.CASCADE, 
        related_name='credit_sales'
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    
    # Amounts
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Credit Sale #{self.id} - {self.customer.name} - KSh {self.balance}"
    
    def save(self, *args, **kwargs):
        # Calculate balance
        self.balance = self.total_amount - self.amount_paid
        
        # Update status
        if self.balance <= 0:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'PENDING'
        
        # Check if overdue
        if self.due_date:
            from django.utils import timezone
            if timezone.now().date() > self.due_date and self.balance > 0:
                self.status = 'OVERDUE'
        
        super().save(*args, **kwargs)
        
        # Update customer total
        self.customer.update_total_credit()


class CreditPayment(models.Model):
    """
    Payments made towards credit sales
    """
    credit_sale = models.ForeignKey(
        CreditSale, 
        on_delete=models.CASCADE, 
        related_name='credit_payments'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=Payment.PAYMENT_METHODS,
        default='CASH'
    )
    
    # M-Pesa details if applicable
    mpesa_transaction_code = models.CharField(max_length=50, blank=True)
    
    # Metadata
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment #{self.id} - KSh {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update credit sale amount paid
        self.credit_sale.amount_paid = self.credit_sale.credit_payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        self.credit_sale.save()