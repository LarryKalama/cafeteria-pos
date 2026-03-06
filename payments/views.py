from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Payment, CreditCustomer, CreditSale, CreditPayment
from .forms import PaymentForm, CreditCustomerForm, CreditPaymentForm
from orders.models import Order

@login_required
def process_payment(request, order_id):
    """Process payment for an order"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment_method = form.cleaned_data['payment_method']
                    
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=payment_method,
                        amount=order.total,
                        processed_by=request.user
                    )
                    
                    if payment_method == 'CASH':
                        payment.amount_tendered = form.cleaned_data['amount_tendered']
                        payment.change_given = payment.amount_tendered - order.total
                        payment.save()
                        
                    elif payment_method == 'MPESA':
                        payment.mpesa_transaction_code = form.cleaned_data['mpesa_code']
                        payment.mpesa_phone_number = form.cleaned_data['mpesa_phone']
                        payment.save()
                        
                    elif payment_method == 'CREDIT':
                        customer_id = form.cleaned_data['credit_customer']
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
                    
                    messages.success(request, 'Payment processed successfully!')
                    return redirect('orders:receipt', pk=order.pk)
                    
            except Exception as e:
                messages.error(request, f'Error processing payment: {str(e)}')
    else:
        form = PaymentForm()
    
    return render(request, 'payments/process_payment.html', {
        'form': form,
        'order': order
    })

@login_required
def credit_customer_list(request):
    """List credit customers"""
    customers = CreditCustomer.objects.all()
    return render(request, 'payments/credit_customer_list.html', {
        'customers': customers
    })

@login_required
def credit_customer_create(request):
    """Create credit customer"""
    if request.method == 'POST':
        form = CreditCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.name} added!')
            return redirect('payments:credit_customer_list')
    else:
        form = CreditCustomerForm()
    
    return render(request, 'payments/credit_customer_form.html', {
        'form': form,
        'title': 'Add Credit Customer'
    })

@login_required
def credit_sale_list(request):
    """List all credit sales"""
    sales = CreditSale.objects.select_related('customer', 'order').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        sales = sales.filter(status=status)
    
    return render(request, 'payments/credit_sale_list.html', {'sales': sales})

@login_required
def credit_sale_detail(request, pk):
    """Credit sale detail with payment recording"""
    sale = get_object_or_404(CreditSale, pk=pk)
    
    if request.method == 'POST':
        form = CreditPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.credit_sale = sale
            payment.received_by = request.user
            payment.save()
            
            messages.success(request, f'Payment of KSh {payment.amount} recorded!')
            return redirect('payments:credit_sale_detail', pk=pk)
    else:
        form = CreditPaymentForm()
    
    payments = sale.credit_payments.all()
    
    return render(request, 'payments/credit_sale_detail.html', {
        'sale': sale,
        'form': form,
        'payments': payments
    })
