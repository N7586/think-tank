import requests
import json
import base64
from datetime import datetime


class OrangeMoneyAPI:
    BASE_URL = 'https://api.orange.com/orange-money-webpay/cm/v1'

    def __init__(self, client_id, client_secret, merchant_key):
        self.client_id = client_id
        self.client_secret = client_secret
        self.merchant_key = merchant_key
        self.access_token = None
        self.token_expires = None

    def get_access_token(self):
        url = 'https://api.orange.com/oauth/v3/token'
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {'grant_type': 'client_credentials'}

        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_expires = datetime.utcnow().timestamp() + token_data.get('expires_in', 3600)
                return True
            return False
        except requests.RequestException:
            return False

    def initiate_payment(self, amount, phone_number, order_id, description='Paiement TSI'):
        if not self.access_token:
            self.get_access_token()

        if not self.access_token:
            return {'status': 'error', 'message': 'Impossible d\'obtenir le token d\'accès'}

        url = f'{self.BASE_URL}/webpayment'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'merchant_key': self.merchant_key,
            'currency': 'XOF',
            'order_id': order_id,
            'amount': amount,
            'return_url': f'https://tsi-institute.org/payment/callback/orange',
            'cancel_url': f'https://tsi-institute.org/payment/cancel/orange',
            'notif_url': f'https://tsi-institute.org/payment/webhook/orange',
            'lang': 'fr',
            'reference': description
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code in [200, 201]:
                return {
                    'status': 'success',
                    'payment_url': response.json().get('payment_url'),
                    'pay_token': response.json().get('pay_token'),
                    'noti_token': response.json().get('noti_token')
                }
            return {'status': 'error', 'message': response.json().get('message', 'Erreur inconnue')}
        except requests.RequestException as e:
            return {'status': 'error', 'message': str(e)}

    def check_payment_status(self, pay_token):
        url = f'{self.BASE_URL}/webpayment/{pay_token}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'payment_status': data.get('status'),
                    'txn_id': data.get('txnid')
                }
            return {'status': 'error', 'message': 'Erreur lors de la vérification'}
        except requests.RequestException as e:
            return {'status': 'error', 'message': str(e)}


class OrangeMoneySimulator:
    """Simulateur Orange Money pour le développement"""

    @staticmethod
    def initiate_payment(amount, phone_number, order_id, description='Paiement TSI'):
        return {
            'status': 'success',
            'payment_url': f'https://pay.orange.com/simulate/{order_id}',
            'pay_token': f'sim_pay_{order_id}',
            'noti_token': f'sim_noti_{order_id}',
            'simulated': True,
            'message': 'Simulation: En production, l\'utilisateur serait redirigé vers Orange Money'
        }

    @staticmethod
    def check_payment_status(pay_token):
        return {
            'status': 'success',
            'payment_status': 'SUCCESS',
            'txn_id': f'TXN-{pay_token[:8]}',
            'simulated': True
        }
