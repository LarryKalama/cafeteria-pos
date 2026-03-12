# payments/utils.py

import requests
import base64
from django.conf import settings

def initiate_stk_push(phone, amount, order_id):
    """
    Initiate M-Pesa STK Push.
    This is a placeholder. Replace with actual Daraja API integration.
    """
    # Example: encode credentials
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = settings.MPESA_STK_PUSH_URL
    shortcode = settings.MPESA_SHORTCODE
    lipa_na_mpesa_passkey = settings.MPESA_PASSKEY
    callback_url = settings.MPESA_CALLBACK_URL

    # Normally you'd generate the access token and call the STK push API
    # Here we just return a dummy success response
    return {
        "order_id": order_id,
        "phone": phone,
        "amount": amount,
        "status": "pending"
    }