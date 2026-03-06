from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import MenuItem, Category
from .forms import MenuItemForm, CategoryForm
from accounts.permissions import (
    can_manage_menu,
    can_adjust_inventory,
    can_record_expenses,
    can_view_reports,
    can_view_inventory,
    is_staff,
    is_superadmin,
)


@login_required
def menuitem_list(request):
    """
    List all active menu items (visible to all logged-in users: waiter, cashier, superadmin).
    """
    try:
        items = MenuItem.objects.select_related('category').filter(is_active=True)
        categories = Category.objects.filter(is_active=True)

        # Optional category filter (safe)
        category_id = request.GET.get('category')
        if category_id:
            try:
                items = items.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass  # invalid category → show all

        return render(request, 'menu/menuitem_list.html', {
            'items': items,
            'categories': categories,
            'selected_category': category_id,
        })

    except Exception as e:
        # Fallback if something breaks (e.g. template missing)
        return render(request, 'menu/menuitem_list.html', {
            'error_message': f"Error loading menu: {str(e)}",
            'items': MenuItem.objects.none(),
            'categories': Category.objects.none(),
            'selected_category': None,
        })


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def menuitem_create(request):
    """Create menu item"""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.is_active = True  # force active so it shows in list
            item.save()

            # Create stock record if tracking inventory
            if item.track_inventory:
                from inventory.models import Stock
                Stock.objects.create(menu_item=item, quantity=0)

            messages.success(request, f'Menu item "{item.name}" created successfully!')
            return redirect('menu:menuitem_list')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = MenuItemForm()

    return render(request, 'menu/menuitem_form.html', {
        'form': form,
        'title': 'Add Menu Item'
    })


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def menuitem_update(request, pk):
    """Update menu item"""
    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Menu item "{item.name}" updated successfully!')
            return redirect('menu:menuitem_list')
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'menu/menuitem_form.html', {
        'form': form,
        'title': f'Update: {item.name}'
    })


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def menuitem_delete(request, pk):
    """Deactivate menu item (soft delete)"""
    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        item.is_active = False
        item.save()
        messages.success(request, f'Menu item "{item.name}" has been deactivated.')
        return redirect('menu:menuitem_list')

    return render(request, 'menu/menuitem_confirm_delete.html', {'item': item})


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def category_list(request):
    """List all active categories"""
    categories = Category.objects.filter(is_active=True)
    return render(request, 'menu/category_list.html', {'categories': categories})


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created!')
            return redirect('menu:category_list')
    else:
        form = CategoryForm()

    return render(request, 'menu/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def category_update(request, pk):
    """Update category"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated!')
            return redirect('menu:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'menu/category_form.html', {
        'form': form,
        'title': f'Update: {category.name}'
    })


@login_required
@user_passes_test(can_manage_menu)  # only superadmin
def category_delete(request, pk):
    """Deactivate category (soft delete)"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name = category.name
        category.is_active = False
        category.save()
        messages.success(request, f'Category "{name}" has been deactivated.')
        return redirect('menu:category_list')

    return render(request, 'menu/category_confirm_delete.html', {'category': category})