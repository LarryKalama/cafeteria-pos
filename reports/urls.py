from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Root: main/full sales report page (superadmin)
    path('', views.sales_report, name='sales_report'),

    # Alternative explicit path for sales report (kept from your first version)
    path('sales/', views.sales_report, name='sales'),

    # Waiter performance report (superadmin only)
    path('waiters/', views.waiter_performance, name='waiter_performance'),

    # Simplified today's summary (cashier & waiter only)
    path('today/', views.today_summary, name='today_summary'),

    # Optional: old commented name (if you ever want to restore it)
    # path('waiter-performance/', views.waiter_performance, name='waiter_performance'),
]