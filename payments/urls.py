from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    # -----------------------------------------------------
    # PAYMENT PROCESSING
    # -----------------------------------------------------
    path(
        "process/<int:order_id>/",
        views.process_payment,
        name="process_payment"
    ),

    # -----------------------------------------------------
    # CREDIT CUSTOMERS
    # -----------------------------------------------------
    path(
        "credit/customers/",
        views.credit_customer_list,
        name="credit_customer_list"
    ),
    path(
        "credit/customers/create/",
        views.credit_customer_create,
        name="credit_customer_create"
    ),

    # -----------------------------------------------------
    # CREDIT SALES
    # -----------------------------------------------------
    path(
        "credit/sales/",
        views.credit_sale_list,
        name="credit_sale_list"
    ),
    path(
        "credit/sales/<int:pk>/",
        views.credit_sale_detail,
        name="credit_sale_detail"
    ),
    path('initiate-stk/<int:order_id>/', views.initiate_stk_push, name='initiate_stk_push'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]