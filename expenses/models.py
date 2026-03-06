from django.db import models
from django.conf import settings
from django.utils import timezone


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Select a predefined category or leave blank for custom"
    )
    custom_category = models.CharField(
        max_length=150,
        blank=True,
        help_text="Use this if the expense doesn't fit any category above"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_paid'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = "Expenses"

    def __str__(self):
        cat = self.category.name if self.category else self.custom_category or "Miscellaneous"
        return f"{cat} - KSH {self.amount} - {self.date}"

    @property
    def display_category(self):
        return self.category.name if self.category else self.custom_category or "Miscellaneous"