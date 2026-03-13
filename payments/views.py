import json
import requests
from base64 import b64encode
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from django.conf import settings
from orders.models import Order
from .models import Payment, CreditCustomer, CreditSale, CreditPayment
from .forms import PaymentForm, CreditCustomerForm, CreditPaymentForm
from .utils import initiate_stk_push  # Your existing M-Pesa utility (if any)


# -----------------------------------------------------
# PROCESS PAYMENT (original + preserved)
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
# CREDIT CUSTOMERS (original - preserved)
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
# CREDIT SALES (original - preserved)
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


# -----------------------------------------------------
# M-PESA STK PUSH - NEW FUNCTIONAL IMPLEMENTATION
# -----------------------------------------------------
def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = b64encode(f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(url, headers=headers)
    return response.json()["access_token"]

@require_POST
@login_required
def initiate_stk_push(request, order_id):
    """
    Initiate Lipa na M-Pesa STK Push for the given order.
    Called via AJAX from order detail page.
    """
    print(f"STK initiation started for order {order_id} by user {request.user}")

    try:
        order = get_object_or_404(Order, id=order_id, status='PENDING')
        print(f"Order found: {order.id}, total: {order.total}")
    except Exception as e:
        print(f"Order fetch error: {str(e)}")
        return JsonResponse({"error": "Order not found or already processed"}, status=404)

    if order.waiter != request.user and not request.user.is_superadmin:
        print("Unauthorized access attempt")
        return JsonResponse({"error": "Unauthorized"}, status=403)

    phone = request.POST.get('phone_number')
    print(f"Phone received: {phone}")

    if not phone or not phone.startswith('254') or len(phone) != 12:
        print("Invalid phone format")
        return JsonResponse({"error": "Invalid phone number (use format 2547XXXXXXXX)"}, status=400)

    try:
        # Create pending payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total,
            payment_method='MPESA',
            processed_by=request.user,
            mpesa_phone_number=phone,
            status='PENDING'  # will change on callback
        )
        print(f"Payment created: ID {payment.id}")
    except Exception as e:
        print(f"Payment creation error: {str(e)}")
        return JsonResponse({"error": f"Failed to create payment record: {str(e)}"}, status=500)

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = b64encode(password_str.encode()).decode()
        print("Password generated successfully")

        # Ensure total is safe to convert
        amount_str = str(int(float(order.total))) if order.total else "0"

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount_str,
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": "https://dollie-exosporous-ricardo.ngrok-free.dev/payments/mpesa-callback/",
            "AccountReference": f"Order-{order.order_number or order.id}",
            "TransactionDesc": f"Payment for order {order.order_number or order.id}",
        }
        print("Payload prepared")

        access_token = get_access_token()
        print("Access token received")

        headers = {"Authorization": f"Bearer {access_token}"}
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        print(f"Sending STK request to {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Daraja response status: {response.status_code}")

        resp_data = response.json()
        print(f"Daraja full response: {resp_data}")

        if resp_data.get("ResponseCode") == "0":
            checkout_id = resp_data.get("CheckoutRequestID")
            if checkout_id:
                payment.checkout_request_id = checkout_id
                payment.save()
                print(f"STK initiated successfully - CheckoutRequestID: {checkout_id}")
                return JsonResponse({
                    "success": True,
                    "message": "STK Push sent. Enter PIN on your phone to complete payment.",
                    "checkout_request_id": checkout_id
                })
            else:
                print("No CheckoutRequestID in success response")
                payment.status = 'FAILED'
                payment.result_description = "Success but missing CheckoutRequestID"
                payment.save()
                return JsonResponse({"error": "Unexpected success response from Daraja"}, status=500)
        else:
            error_msg = resp_data.get("ErrorMessage", resp_data.get("CustomerMessage", "Unknown error"))
            print(f"STK failed: {error_msg}")
            payment.status = 'FAILED'
            payment.result_description = error_msg
            payment.save()
            return JsonResponse({"error": error_msg}, status=400)

    except Exception as e:
        print(f"Critical STK initiation error: {str(e)}")
        if 'payment' in locals():
            payment.status = 'FAILED'
            payment.result_description = str(e)
            payment.save()
        return JsonResponse({"error": f"Failed to initiate payment: {str(e)}"}, status=500)
@csrf_exempt
def mpesa_callback(request):
    """
    Handle Daraja callback after STK Push transaction.
    Updates payment and order status when PIN is entered successfully.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            body = data['Body']['stkCallback']

            checkout_request_id = body['CheckoutRequestID']
            result_code = body['ResultCode']
            result_desc = body['ResultDesc']

            payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()

            if not payment:
                return HttpResponse("Payment not found")

            payment.result_code = result_code
            payment.result_description = result_desc
            payment.callback_received_at = timezone.now()

            if result_code == 0:
                # Success - extract receipt number
                payment.status = 'COMPLETED'
                if 'CallbackMetadata' in body:
                    metadata = body['CallbackMetadata']['Item']
                    for item in metadata:
                        if item['Name'] == 'MpesaReceiptNumber':
                            payment.mpesa_receipt_number = item['Value']
                            break

                # Complete the order
                payment.order.status = 'COMPLETED'
                payment.order.save()

            else:
                payment.status = 'FAILED'

            payment.save()
            return HttpResponse("Callback received")

        except Exception as e:
            print("M-Pesa callback error:", str(e))
            return HttpResponse("Error processing callback")

    return HttpResponse("Method not allowed", status=405)