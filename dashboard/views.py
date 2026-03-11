from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F
from orders.models import Order
from inventory.models import Stock
from payments.models import CreditSale  # adjust if CreditSale is in different app

@login_required
def home(request):
    """
    Main dashboard - role-based view
    """
    user = request.user
    today = timezone.now().date()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if user.is_superadmin:
        # Superadmin dashboard - full stats
        today_orders = Order.objects.filter(created_at__gte=today_start)

        today_sales = 0
        if user.role == 'SUPERADMIN':  # Only superadmin sees sales amount
            today_sales = today_orders.aggregate(total=Sum('total'))['total'] or 0

        pending_credit = CreditSale.objects.filter(
            status__in=['PENDING', 'PARTIAL', 'OVERDUE']
        ).aggregate(total=Sum('balance'))['total'] or 0

        low_stock_items = Stock.objects.filter(
            quantity__lte=F('reorder_level')
        ).select_related('menu_item')

        recent_orders = Order.objects.select_related('waiter').order_by('-created_at')[:10]

        context = {
            'today_orders_count': today_orders.count(),
            'today_sales': today_sales,  # 0 for non-superadmin (but only shown to superadmin)
            'pending_credit': pending_credit,
            'low_stock_items': low_stock_items,
            'low_stock_count': low_stock_items.count(),
            'recent_orders': recent_orders,
            'user_role': user.role,
            'title': 'Cafeteria POS Dashboard',
        }

    else:
        # Waiter/Cashier dashboard - limited stats (no full sales visibility)
        waiter_orders_today = Order.objects.filter(
            waiter=user,
            created_at__gte=today_start
        )

        context = {
            'orders_today': waiter_orders_today.count(),
            'recent_orders': waiter_orders_today.order_by('-created_at')[:10],
            'user_role': user.role,
            'title': 'Cafeteria POS Dashboard',
        }

    return render(request, 'dashboard/home.html', context)