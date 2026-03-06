from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<int:order_id>/', views.process_payment, name='process_payment'),
    path('credit/customers/', views.credit_customer_list, name='credit_customer_list'),
    path('credit/customers/create/', views.credit_customer_create, name='credit_customer_create'),
    path('credit/sales/', views.credit_sale_list, name='credit_sale_list'),
    path('credit/sales/<int:pk>/', views.credit_sale_detail, name='credit_sale_detail'),
]