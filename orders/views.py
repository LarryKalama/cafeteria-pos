from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import Order, OrderItem
from menu.models import MenuItem, Category
import json
from django.urls import reverse
@login_required
def create_order(request):
    """Create new order with cart system"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                customer_name = request.POST.get('customer_name', '')
                table_number = request.POST.get('table_number', '')
                cart_data = json.loads(request.POST.get('cart_data', '[]'))
                
                if not cart_data:
                    messages.error(request, 'Cart is empty!')
                    return redirect('orders:create')
                
                # Create order
                order = Order.objects.create(
                    waiter=request.user,
                    customer_name=customer_name,
                    table_number=table_number,
                    status='PENDING'
                )
                
                # Add items
                for item in cart_data:
                    menu_item = MenuItem.objects.get(id=item['id'])
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=item['quantity'],
                        unit_price=menu_item.selling_price,
                        notes=item.get('notes', '')
                    )
                # Add this line
                order.calculate_totals()  # ← recalculate subtotal, tax, total

                messages.success(request, f'Order #{order.order_number} created successfully!')
                return redirect('orders:order_detail', pk=order.pk)
                
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('orders:create_order')
    
    # GET request - show menu
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    return render(request, 'orders/create_order.html', {
        'categories': categories
    })

@login_required
def order_list(request):
    """List all orders"""
    orders = Order.objects.select_related('waiter').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by waiter (non-superadmins see only their orders)
    if not request.user.is_superadmin:
        orders = orders.filter(waiter=request.user)
    
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    """Order details"""
    order = get_object_or_404(Order, pk=pk)

    # Check permissions
    if not request.user.is_superadmin and order.waiter != request.user:
        messages.error(request, 'You can only view your own orders!')
        return redirect('orders:order_list')  # ← corrected name to match your urls

    # Add process_payment_url to context for the payment form include
    context = {
        'order': order,
        'process_payment_url': reverse('orders:process_payment', args=[order.pk]),
    }

    return render(request, 'orders/order_detail.html', context)
@login_required
def kitchen_ticket(request, pk):
    """Print kitchen ticket"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/kitchen_ticket.html', {'order': order})

@login_required
def print_receipt(request, pk):
    """Print customer receipt"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/receipt.html', {'order': order})
# orders/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Order
from pos.utils.mpesa import lipa_na_mpesa_online  # assuming you created this file
import json


@csrf_exempt
def mpesa_callback(request):
    """
    M-Pesa Daraja callback endpoint.
    Daraja sends payment result here asynchronously.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        callback = data.get('Body', {}).get('stkCallback', {})

        result_code = callback.get('ResultCode')
        checkout_request_id = callback.get('CheckoutRequestID')
        result_desc = callback.get('ResultDesc', '')

        # You can log the full callback for debugging
        # print("M-Pesa Callback:", data)

        if result_code == 0:
            # Payment successful
            # Find order by CheckoutRequestID (you saved it when initiating)
            try:
                order = Order.objects.get(checkout_request_id=checkout_request_id)
                order.status = 'PAID'
                order.payment_method = 'MPESA'
                order.paid_at = timezone.now()
                order.save()

                # Optional: create payment record
                # Payment.objects.create(order=order, amount=order.total, payment_method='MPESA', status='SUCCESS')

                return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
            except Order.DoesNotExist:
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Order not found"})
        else:
            # Payment failed or cancelled
            # Optional: update order status to 'FAILED' or leave as PENDING
            return JsonResponse({"ResultCode": result_code, "ResultDesc": result_desc})

    except Exception as e:
        # Log error in production
        print("M-Pesa callback error:", str(e))
        return JsonResponse({"error": "Internal error"}, status=500)


@login_required
def initiate_mpesa_payment(request, order_id):
    """
    Initiate STK Push for an existing order.
    Called when user clicks "Pay with M-Pesa" on checkout/confirm page.
    """
    order = get_object_or_404(Order, id=order_id, waiter=request.user)  # or adjust permission

    if order.status != 'PENDING':
        messages.error(request, "This order is already processed.")
        return redirect('orders:order_detail', order.pk)

    if request.method == 'POST':
        phone = request.POST.get('phone_number')

        # Basic validation
        if not phone or len(phone) != 12 or not phone.startswith('2547'):
            messages.error(request, "Please enter a valid Kenyan phone number (e.g. 254712345678)")
            return redirect(request.path)

        # Save checkout request ID so we can match callback
        response = lipa_na_mpesa_online(
            phone_number=phone,
            amount=int(order.total),
            order_id=order.id,
        )

        if response.get('ResponseCode') == '0':
            # STK Push initiated successfully
            checkout_request_id = response['CheckoutRequestID']
            order.checkout_request_id = checkout_request_id  # save for callback matching
            order.save()

            messages.success(request, "Please check your phone and enter PIN to complete payment.")
            return redirect('orders:wait_for_mpesa_payment', order.pk)
        else:
            error_msg = response.get('errorMessage', 'Failed to initiate payment')
            messages.error(request, f"M-Pesa error: {error_msg}")
            return redirect(request.path)

    # GET request → show phone input form
    return render(request, 'orders/confirm_payment.html', {'order': order})

@login_required
def wait_for_mpesa_payment(request, order_id):
    """
    Shows a waiting screen after STK Push is initiated.
    User is told to enter PIN on their phone.
    """
    order = get_object_or_404(Order, id=order_id, waiter=request.user)

    # Optional: check if payment is already completed (via polling or callback)
    # For now, simple waiting page

    context = {
        'order': order,
        'title': f"Waiting for M-Pesa Payment - Order #{order.order_number}",
    }
    return render(request, 'orders/wait_for_mpesa_payment.html', context)


@login_required
def mark_paid_cash(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.status != 'PENDING':
        messages.error(request, "Order is already processed.")
        return redirect('orders:order_detail', order.pk)

    if request.method == 'POST':
        # Mark as paid with cash
        order.status = 'PAID'
        order.payment_method = 'CASH'
        order.paid_at = timezone.now()
        order.save()

        messages.success(request, "Order marked as paid with cash.")
        return redirect('orders:order_detail', order.pk)

    # Show confirmation page
    return render(request, 'orders/confirm_cash_payment.html', {'order': order})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order
from payments.models import Payment  # assuming Payment model is in payments app


@login_required
def process_payment(request, pk):
    """
    Unified payment processing view.
    Handles Cash, M-Pesa, and Credit payments via the shared form.
    """
    order = get_object_or_404(Order, pk=pk)

    # Only allow processing PENDING orders
    if order.status != 'PENDING':
        messages.error(request, "Order already processed.")
        return redirect('orders:order_detail', order.pk)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash').lower()

        # Create unified Payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total,
            payment_method=payment_method.upper(),
            processed_by=request.user,
        )

        # Method-specific logic
        if payment_method == 'cash':
            amount_tendered = float(request.POST.get('amount_tendered', 0))
            change = amount_tendered - order.total
            payment.amount_tendered = amount_tendered
            payment.change_given = change if change > 0 else 0
            payment.save()

        elif payment_method == 'mpesa':
            payment.mpesa_transaction_code = request.POST.get('mpesa_code', '').strip()
            payment.mpesa_phone_number = request.POST.get('mpesa_phone', '').strip()
            payment.save()

        elif payment_method == 'credit':
            payment.credit_customer_name = request.POST.get('credit_customer', '').strip()
            payment.save()

        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('orders:order_detail', order.pk)

        # Mark order as completed
        order.status = 'COMPLETED'  # or 'PAID' — choose your final status
        order.paid_at = timezone.now()
        order.save()

        messages.success(request, f"Payment completed via {payment_method.capitalize()}.")
        return redirect('orders:order_detail', order.pk)

    # GET request → redirect back (should not happen if form is correct)
    return redirect('orders:order_detail', order.pk)