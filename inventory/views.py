from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import F
from .models import Stock, StockTransaction
from .forms import StockForm, StockAddForm, StockAdjustmentForm
from accounts.permissions import can_manage_stock, can_view_stock

@login_required
@user_passes_test(can_manage_stock)
def stock_list(request):
    """
    List all stock entries (visible to superadmin, cashier, waiter).
    Supports filtering: ?filter=low or ?filter=out
    """
    # Load all stock with related menu_item and category (efficient)
    stocks = Stock.objects.select_related('menu_item__category').all()

    # Optional filter from query param
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'low':
        # Low stock: quantity <= reorder_level AND not already 0
        stocks = stocks.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
    elif filter_type == 'out':
        stocks = stocks.filter(quantity=0)

    # Compute alert counts for template (efficient .count() instead of looping)
    low_stock_count = Stock.objects.filter(
        quantity__lte=F('reorder_level'),
        quantity__gt=0
    ).count()
    out_of_stock_count = Stock.objects.filter(quantity=0).count()

    context = {
        'stocks': stocks,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'title': 'Stock Levels',
        'can_manage_stock': can_manage_stock(request.user),  # makes Edit/Delete visible
    }

    return render(request, 'inventory/stock_list.html', context)
@login_required
@user_passes_test(can_manage_stock)
def stock_add(request):
    """
    Add / receive new stock for a menu item (separate add form).
    """
    if request.method == 'POST':
        form = StockAddForm(request.POST)
        if form.is_valid():
            menu_item = form.cleaned_data['menu_item']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']

            # Get or create stock record
            stock, created = Stock.objects.get_or_create(menu_item=menu_item)
            stock.quantity += quantity
            stock.notes = notes or stock.notes
            stock.save()

            # Optional: log transaction
            StockTransaction.objects.create(
                stock=stock,
                transaction_type='IN',
                quantity=quantity,
                balance_after=stock.quantity,
                notes=notes,
                user=request.user
            )

            messages.success(request, f"Added {quantity} of {menu_item.name} to stock")
            return redirect('inventory:stock_list')
    else:
        form = StockAddForm()

    return render(request, 'inventory/stock_form.html', {
        'form': form,
        'title': 'Add / Receive Stock',
    })


@login_required
@user_passes_test(can_manage_stock)
def stock_edit(request, pk):
    """
    Edit existing stock record (quantity, reorder level, etc.).
    """
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, f"Stock for {stock.menu_item.name} updated")
            return redirect('inventory:stock_list')
    else:
        form = StockForm(instance=stock)

    return render(request, 'inventory/stock_form.html', {
        'form': form,
        'title': f'Edit Stock: {stock.menu_item.name}',
    })


@login_required
@user_passes_test(can_manage_stock)
def stock_adjust(request, pk):
    """
    Quick stock adjustment (add or remove quantity) using StockAdjustmentForm.
    """
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']

            if transaction_type == 'IN':
                stock.quantity += quantity
            else:
                if stock.quantity < quantity:
                    messages.error(request, f"Not enough stock to remove {quantity} from {stock.menu_item.name}")
                    return redirect('inventory:stock_adjust', pk=pk)
                stock.quantity -= quantity

            stock.notes = notes or stock.notes
            stock.save()

            # Log the transaction
            StockTransaction.objects.create(
                stock=stock,
                transaction_type=transaction_type,
                quantity=quantity,
                balance_after=stock.quantity,
                notes=notes,
               user=request.user
            )

            messages.success(request, f"{transaction_type} {quantity} for {stock.menu_item.name}")
            return redirect('inventory:stock_list')
    else:
        form = StockAdjustmentForm()

    return render(request, 'inventory/stock_adjust.html', {
        'form': form,
        'stock': stock,
        'title': f'Adjust Stock: {stock.menu_item.name}',
    })


@login_required
@user_passes_test(can_manage_stock)
def stock_delete(request, pk):
    """
    Delete stock entry (only if allowed).
    """
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == 'POST':
        menu_item_name = stock.menu_item.name
        stock.delete()
        messages.success(request, f"Stock entry for {menu_item_name} deleted")
        return redirect('inventory:stock_list')

    return render(request, 'inventory/stock_confirm_delete.html', {
        'stock': stock,
        'title': 'Confirm Delete Stock Entry',
    })


@login_required
@user_passes_test(can_view_stock)
def stock_transactions(request, pk):
    """
    View transaction history for a specific stock item.
    """
    stock = get_object_or_404(Stock, pk=pk)
    transactions = stock.transactions.all().order_by('-created_at')[:50]

    return render(request, 'inventory/stock_transactions.html', {
        'stock': stock,
        'transactions': transactions,
        'title': f'Transactions for {stock.menu_item.name}',
    })