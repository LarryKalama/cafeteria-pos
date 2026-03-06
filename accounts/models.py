from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User Model with roles
    """
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Admin'),
        ('WAITER', 'Waiter'),
        ('CASHIER', 'Cashier'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='WAITER')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_superadmin(self):
        return self.role == 'SUPERADMIN'
    
    @property
    def is_waiter(self):
        return self.role == 'WAITER'
    
    @property
    def is_cashier(self):
        return self.role == 'CASHIER'
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username