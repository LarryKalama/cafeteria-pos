# payments/views.py

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .models import Payment, CreditCustomer, CreditSale, CreditPayment
from .forms import PaymentForm, CreditCustomerForm, CreditPaymentForm
from .utils import initiate_stk_push  # Your M-Pesa utility function


# -----------------------------------------------------
# PROCESS PAYMENT
# -----------------------------------------------------
@login_required
def process_payment(request, order_id):
    """
    Process payment for an order.
    Supports CASH, MPESA, and CREDIT payments.
    """
    order = get_object_or_404(Order, pk=order_id)

    # Prevent duplicate payment
    if order.status == "COMPLETED":
        messages.warning(request, "This order has already been paid.")
        return redirect('orders:order_detail', pk=order.pk)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():

                    payment_method = form.cleaned_data['payment_method']

                    # Create base payment record
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=payment_method,
                        amount=order.total,
                        processed_by=request.user
                    )

                    # ------------------------
                    # CASH PAYMENT
                    # ------------------------
                    if payment_method == "CASH":
                        amount_tendered = form.cleaned_data.get("amount_tendered")
                        payment.amount_tendered = float(amount_tendered)
                        payment.change_given = float(amount_tendered) - float(order.total)
                        payment.save()

                    # ------------------------
                    # MPESA PAYMENT
                    # ------------------------
                    elif payment_method == "MPESA":
                        payment.mpesa_phone_number = form.cleaned_data.get("mpesa_phone")
                        payment.mpesa_transaction_code = form.cleaned_data.get("mpesa_code")
                        payment.save()

                    # ------------------------
                    # CREDIT PAYMENT
                    # ------------------------
                    elif payment_method == "CREDIT":
                        customer_id = form.cleaned_data.get("credit_customer")
                        if customer_id:
                            customer = CreditCustomer.objects.get(id=customer_id)
                            payment.credit_customer = customer
                            payment.save()

                            # Create credit sale record
                            CreditSale.objects.create(
                                customer=customer,
                                order=order,
                                total_amount=order.total,
                                balance=order.total,
                                created_by=request.user
                            )

                    # Mark order as completed
                    order.mark_completed()

                    messages.success(request, "Payment processed successfully!")
                    return redirect("orders:receipt", pk=order.pk)

            except Exception as e:
                messages.error(request, f"Error processing payment: {str(e)}")
        else:
            messages.error(request, "Invalid payment data submitted.")

    else:
        form = PaymentForm()

    return render(request, "orders/order_detail.html", {
        "form": form,
        "order": order
    })


# -----------------------------------------------------
# MPESA STK PUSH ENDPOINT
# -----------------------------------------------------
@login_required
@csrf_exempt
def mpesa_stk_push(request, order_id):
    """
    Trigger M-Pesa STK Push for an order.
    Expects JSON payload: { "phone": "2547XXXXXXXX" }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get("phone")
            order = get_object_or_404(Order, pk=order_id)
            amount = order.total

            response = initiate_stk_push(phone, amount, order_id)

            return JsonResponse({"success": True, "message": "STK Push sent", "data": response})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# -----------------------------------------------------
# CREDIT CUSTOMERS
# -----------------------------------------------------
@login_required
def credit_customer_list(request):
    """List all credit customers"""
    customers = CreditCustomer.objects.all().order_by("name")
    return render(request, "payments/credit_customer_list.html", {"customers": customers})


@login_required
def credit_customer_create(request):
    """Create a new credit customer"""
    if request.method == "POST":
        form = CreditCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' added successfully.")
            return redirect("payments:credit_customer_list")
    else:
        form = CreditCustomerForm()

    return render(request, "payments/credit_customer_form.html", {
        "form": form,
        "title": "Add Credit Customer"
    })


# -----------------------------------------------------
# CREDIT SALES
# -----------------------------------------------------
@login_required
def credit_sale_list(request):
    """List all credit sales"""
    sales = CreditSale.objects.select_related("customer", "order").order_by("-created_at")

    # Filter by status
    status = request.GET.get("status")
    if status:
        sales = sales.filter(status=status)

    return render(request, "payments/credit_sale_list.html", {"sales": sales})


@login_required
def credit_sale_detail(request, pk):
    """
    Detail of a credit sale.
    Allows recording payments to reduce balance.
    """
    sale = get_object_or_404(CreditSale, pk=pk)

    if request.method == "POST":
        form = CreditPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.credit_sale = sale
            payment.received_by = request.user
            payment.save()

            # Update remaining balance
            sale.balance -= payment.amount
            if sale.balance <= 0:
                sale.balance = 0
                sale.status = "PAID"
            sale.save()

            messages.success(request, f"Payment of KSh {payment.amount} recorded successfully.")
            return redirect("payments:credit_sale_detail", pk=pk)
    else:
        form = CreditPaymentForm()

    payments = sale.credit_payments.all().order_by("-created_at")

    return render(request, "payments/credit_sale_detail.html", {
        "sale": sale,
        "form": form,
        "payments": payments
    })