from django import forms
from .models import CreditCustomer, CreditPayment

class PaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('MPESA', 'M-Pesa'),
        ('CREDIT', 'Credit'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Cash fields
    amount_tendered = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # M-Pesa fields
    mpesa_code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mpesa_phone = forms.CharField(
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Credit fields
    credit_customer = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CreditCustomerForm(forms.ModelForm):
    class Meta:
        model = CreditCustomer
        fields = ['name', 'phone_number', 'email', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class CreditPaymentForm(forms.ModelForm):
    class Meta:
        model = CreditPayment
        fields = ['amount', 'payment_method', 'mpesa_transaction_code', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'mpesa_transaction_code': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
