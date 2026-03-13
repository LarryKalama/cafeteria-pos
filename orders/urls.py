from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('list/', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/kitchen-ticket/', views.kitchen_ticket, name='kitchen_ticket'),
    path('<int:pk>/receipt/', views.print_receipt, name='receipt'),
    # M-Pesa payment initiation (user enters phone & confirms)
    path('order/<int:order_id>/pay-mpesa/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    # Wait-for-payment page (shows "Enter PIN on phone")
    path('order/<int:order_id>/mpesa-wait/', views.wait_for_mpesa_payment, name='wait_for_mpesa_payment'),
    # Daraja callback (public endpoint)
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('order/<int:pk>/pay-cash/', views.mark_paid_cash, name='mark_paid_cash'),
path('order/<int:pk>/process-payment/', views.process_payment, name='process_payment'),
path('order/<int:pk>/receipt/', views.receipt, name='receipt'),
    path('api/sync-offline/', views.sync_offline, name='sync_offline'),
]
