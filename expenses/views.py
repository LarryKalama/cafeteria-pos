from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv
import logging

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm
from accounts.permissions import can_manage_expenses

logger = logging.getLogger(__name__)


@login_required
def expense_create(request):
    """
    Lightweight expense creation (can be used as quick-add or fallback)
    """
    if request.method == 'POST':
        try:
            description = request.POST.get('description')
            amount = request.POST.get('amount')

            if not description or not amount:
                messages.error(request, "Description and amount are required.")
                return redirect('dashboard:home')

            # Create expense (minimal version - expand later if needed)
            Expense.objects.create(
                description=description,
                amount=amount,
                paid_by=request.user,
                date=timezone.now().date()
            )
            messages.success(request, "Expense recorded!")
            return redirect('dashboard:home')
        except Exception as e:
            logger.error(f"Quick expense create failed: {str(e)}", exc_info=True)
            messages.error(request, f"Failed to record expense: {str(e)}")
            return redirect('dashboard:home')

    return render(request, 'expenses/expense_form.html')


@login_required
@user_passes_test(can_manage_expenses)
def expense_list(request):
    """List expenses with summary and filters"""
    try:
        expenses = Expense.objects.select_related('category', 'paid_by').all()

        # Filters
        category_id = request.GET.get('category')
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')

        if category_id:
            expenses = expenses.filter(category_id=category_id)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        # Summary
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        monthly_total = expenses.filter(
            date__month=timezone.now().month,
            date__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Category breakdown
        category_summary = expenses.values(
            'category__name', 'custom_category'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')

        context = {
            'expenses': expenses,
            'total_expenses': total_expenses,
            'monthly_total': monthly_total,
            'category_summary': category_summary,
            'categories': ExpenseCategory.objects.all(),
            'title': 'Expenses',
        }
        return render(request, 'expenses/expense_list.html', context)

    except Exception as e:
        logger.error(f"Expense list view error: {str(e)}", exc_info=True)
        messages.error(request, f"Error loading expenses: {str(e)}")
        return render(request, 'expenses/expense_list.html', {
            'expenses': [],
            'total_expenses': 0,
            'monthly_total': 0,
            'category_summary': [],
            'categories': [],
            'title': 'Expenses'
        })


@login_required
@user_passes_test(can_manage_expenses)
def expense_add(request):
    """Add new expense"""
    try:
        if request.method == 'POST':
            form = ExpenseForm(request.POST)
            if form.is_valid():
                expense = form.save(commit=False)
                expense.paid_by = request.user
                expense.save()
                messages.success(request, "Expense added successfully.")
                return redirect('expenses:expense_list')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = ExpenseForm()

        return render(request, 'expenses/expense_form.html', {
            'form': form,
            'title': 'Add Expense',
        })

    except Exception as e:
        logger.error(f"Expense add error: {str(e)}", exc_info=True)
        messages.error(request, f"Error adding expense: {str(e)}")
        return redirect('expenses:expense_list')


@login_required
@user_passes_test(can_manage_expenses)
def expense_edit(request, pk):
    """Edit existing expense"""
    try:
        expense = get_object_or_404(Expense, pk=pk)

        if request.method == 'POST':
            form = ExpenseForm(request.POST, instance=expense)
            if form.is_valid():
                form.save()
                messages.success(request, "Expense updated.")
                return redirect('expenses:expense_list')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = ExpenseForm(instance=expense)

        return render(request, 'expenses/expense_form.html', {
            'form': form,
            'title': 'Edit Expense',
        })

    except Exception as e:
        logger.error(f"Expense edit error (pk={pk}): {str(e)}", exc_info=True)
        messages.error(request, f"Error editing expense: {str(e)}")
        return redirect('expenses:expense_list')


@login_required
@user_passes_test(can_manage_expenses)
def expense_delete(request, pk):
    """Delete expense with confirmation"""
    try:
        expense = get_object_or_404(Expense, pk=pk)

        if request.method == 'POST':
            expense.delete()
            messages.success(request, "Expense deleted.")
            return redirect('expenses:expense_list')

        return render(request, 'expenses/expense_confirm_delete.html', {
            'expense': expense,
            'title': 'Confirm Delete Expense',
        })

    except Exception as e:
        logger.error(f"Expense delete error (pk={pk}): {str(e)}", exc_info=True)
        messages.error(request, f"Error deleting expense: {str(e)}")
        return redirect('expenses:expense_list')


@login_required
@user_passes_test(can_manage_expenses)
def expense_export_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Category', 'Custom Category', 'Amount (KSh)',
            'Description', 'Paid By', 'Created At'
        ])

        expenses = Expense.objects.select_related('category', 'paid_by').all()

        # Apply same filters as list view if needed
        category_id = request.GET.get('category')
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')

        if category_id:
            expenses = expenses.filter(category_id=category_id)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        for exp in expenses:
            writer.writerow([
                exp.date.strftime('%Y-%m-%d') if exp.date else '',
                exp.category.name if exp.category else '',
                exp.custom_category or '',
                exp.amount,
                exp.description or '',
                exp.paid_by.get_full_name() if exp.paid_by else (exp.paid_by.username if exp.paid_by else ''),
                exp.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    except Exception as e:
        logger.error(f"Expense CSV export error: {str(e)}", exc_info=True)
        messages.error(request, f"Error exporting expenses: {str(e)}")
        return redirect('expenses:expense_list')