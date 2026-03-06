from django import forms
from .models import Stock
from menu.models import MenuItem


class StockAdjustmentForm(forms.Form):
    """
    Unified form for adding or removing stock (IN/OUT transactions).
    Useful for quick adjustments without full stock record editing.
    """
    TRANSACTION_TYPES = [
        ('IN', 'Add Stock'),
        ('OUT', 'Remove Stock'),
    ]

    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Transaction Type"
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Quantity"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Notes (optional)"
    )

class StockForm(forms.ModelForm):
    """
    ModelForm for editing existing stock records.
    Allows changing quantity, reorder level, unit, notes, etc.
    """

    class Meta:
        model = Stock
        fields = ['menu_item', 'quantity', 'unit', 'custom_unit', 'reorder_level', 'notes']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'custom_unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specify unit (e.g. dozen, crate)',
            }),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make unit and reorder_level optional (so existing blank records don't error)
        self.fields['unit'].required = False
        self.fields['reorder_level'].required = False

        # custom_unit is never required (only shown/used when unit == 'other')
        self.fields['custom_unit'].required = False

        # Optional: set default values if blank (only for new records)
        if not self.instance.pk:
            self.fields['unit'].initial = 'pcs'
            self.fields['reorder_level'].initial = 5
            self.fields['custom_unit'].widget.attrs.update({'placeholder': 'Specify unit'})
class StockAddForm(forms.Form):
    """
    Form for adding/receiving new stock (select menu item + quantity).
    Used when introducing stock for a new menu item or doing bulk receive.
    """
    menu_item = forms.ModelChoiceField(
        queryset=MenuItem.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Menu Item"
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Quantity to Add"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Notes (optional)"
    )