from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem
from payments.models import Payment
from accounts.models import User
from accounts.permissions import can_view_reports


def is_superadmin(user):
    return user.is_authenticated and user.role == 'SUPERADMIN'


@login_required
@user_passes_test(is_superadmin)
def sales_report(request):
    """
    Sales analytics report with period filtering (full version - superadmin only)
    """
    # Default: last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # User-selected period
    period = request.GET.get('period', '30days')

    if period == 'today':
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif period == 'this_month':
        start_date = end_date.replace(day=1)
    elif period == 'custom' and 'start' in request.GET and 'end' in request.GET:
        try:
            start_date = timezone.datetime.strptime(request.GET['start'], '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(request.GET['end'], '%Y-%m-%d').date()
        except:
            pass  # fallback to default

    # Filter completed/paid orders in the period
    orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status__in=['PAID', 'COMPLETED']  # adjust statuses if your model uses different values
    )

    # Basic metrics
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = orders.count()
    average_order = orders.aggregate(avg=Avg('total'))['avg'] or 0

    # Payment methods breakdown
    payments = Payment.objects.filter(order__created_at__gte=start_date)
    payment_breakdown = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Daily sales (for chart or summary)
    daily_sales = orders.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('day')

    # Top selling items
    top_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__name'
    ).annotate(
        qty_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('unit_price'))  # adjust field name if your OrderItem has different pricing
    ).order_by('-qty_sold')[:10]

    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order': round(average_order, 2),
        'payment_breakdown': payment_breakdown,
        'daily_sales': list(daily_sales),
        'top_items': top_items,
        'title': 'Sales Analytics',
    }

    return render(request, 'reports/sales_report.html', context)


@login_required
@user_passes_test(is_superadmin)
def waiter_performance(request):
    """
    Waiter performance report: orders count, total sales, average per waiter (superadmin only)
    """
    # Same period logic as sales_report
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # default

    period = request.GET.get('period', '30days')

    if period == 'today':
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif period == 'this_month':
        start_date = end_date.replace(day=1)
    elif period == 'custom' and 'start' in request.GET and 'end' in request.GET:
        try:
            start_date = timezone.datetime.strptime(request.GET['start'], '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(request.GET['end'], '%Y-%m-%d').date()
        except:
            pass

    # Get all waiters
    waiters = User.objects.filter(role='WAITER')

    waiter_stats = []

    for waiter in waiters:
        waiter_orders = Order.objects.filter(
            waiter=waiter,
            created_at__date__range=[start_date, end_date],
            status__in=['PAID', 'COMPLETED']  # adjust statuses if needed
        )

        total_orders = waiter_orders.count()
        total_sales = waiter_orders.aggregate(total=Sum('total'))['total'] or 0
        avg_sale = total_sales / total_orders if total_orders > 0 else 0

        waiter_stats.append({
            'waiter': waiter,
            'username': waiter.username,
            'full_name': waiter.get_full_name() or waiter.username,
            'total_orders': total_orders,
            'total_sales': total_sales,
            'average_sale': round(avg_sale, 2),
        })

    # Sort by total sales descending
    waiter_stats.sort(key=lambda x: x['total_sales'], reverse=True)

    context = {
        'title': 'Waiter Performance',
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'waiter_stats': waiter_stats,
        'top_waiter': waiter_stats[0] if waiter_stats else None,
    }

    return render(request, 'reports/waiter_performance.html', context)


@login_required
@user_passes_test(lambda u: u.role in ['CASHIER', 'WAITER'])
def today_summary(request):
    """
    Simplified dashboard for cashier/waiter: only today's top items + total orders
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's completed/paid orders
    today_orders = Order.objects.filter(
        created_at__gte=today_start,
        status__in=['PAID', 'COMPLETED']
    )

    total_orders_today = today_orders.count()

    # Top selling items today
    top_items_today = OrderItem.objects.filter(
        order__in=today_orders
    ).values(
        'menu_item__name'
    ).annotate(
        qty_sold=Sum('quantity')
    ).order_by('-qty_sold')[:10]

    context = {
        'title': "Today's Quick Summary",
        'total_orders_today': total_orders_today,
        'top_items_today': top_items_today,
        'today_date': today_start.date(),
    }

    return render(request, 'reports/today_summary.html', context)