import requests
import base64
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth


def get_mpesa_access_token():
    """Get OAuth access token from Daraja"""
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    if settings.MPESA_ENVIRONMENT == 'production':
        api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        api_url,
        auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
    )

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to get M-Pesa access token")


def lipa_na_mpesa_online(phone_number, amount, order_id, callback_url=None):
    """
    Initiate STK Push (Lipa na M-Pesa Online)
    phone_number: format 2547XXXXXXXX
    amount: int
    order_id: your internal order reference
    """
    access_token = get_mpesa_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
    ).decode('utf-8')

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",  # or "CustomerBuyGoodsOnline" for Till
        "Amount": str(amount),
        "PartyA": phone_number,               # customer's number
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url or settings.MPESA_CALLBACK_URL,
        "AccountReference": f"Order-{order_id}",
        "TransactionDesc": f"Payment for Order #{order_id}"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    if settings.MPESA_ENVIRONMENT == 'production':
        api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    response = requests.post(api_url, json=payload, headers=headers)

    return response.json()