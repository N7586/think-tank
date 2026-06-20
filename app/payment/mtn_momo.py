import requests
import json
from datetime import datetime


class MTNMoMoAPI:
    BASE_URL = 'https://sandbox.momodeveloper.mtn.com'

    def __init__(self, api_user, api_key, subscription_key, environment='sandbox'):
        self.api_user = api_user
        self.api_key = api_key
        self.subscription_key = subscription_key
        self.environment = environment
        self.access_token = None
        self.token_expires = None

        if environment == 'production':
            self.BASE_URL = 'https://proxy.momoapi.mtn.com'

    def get_access_token(self):
        url = f'{self.BASE_URL}/collection/token/'
        credentials = f'{self.api_user}:{self.api_key}'
        headers = {
            'Authorization': f'Basic {__import__("base64").b64encode(credentials.encode()).decode()}',
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }

        try:
            response = requests.post(url, headers=headers, timeout=30)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_expires = datetime.utcnow().timestamp() + token_data.get('expires_in', 3600)
                return True
            return False
        except requests.RequestException:
            return False

    def request_to_pay(self, amount, phone_number, external_id, payer_message='Paiement TSI', payee_note='TSI Payment'):
        if not self.access_token:
            self.get_access_token()

        if not self.access_token:
            return {'status': 'error', 'message': 'Impossible d\'obtenir le token d\'accès'}

        reference_id = f'TSI-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-{external_id[:8]}'
        url = f'{self.BASE_URL}/collection/v1_0/requesttopay'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Reference-Id': reference_id,
            'X-Target-Environment': self.environment,
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'amount': str(amount),
            'currency': 'XOF',
            'externalId': external_id,
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone_number
            },
            'payerMessage': payer_message,
            'payeeNote': payee_note
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code in [200, 201, 202]:
                return {
                    'status': 'success',
                    'reference_id': reference_id,
                    'message': 'Paiement initié avec succès'
                }
            return {'status': 'error', 'message': response.json().get('message', 'Erreur inconnue')}
        except requests.RequestException as e:
            return {'status': 'error', 'message': str(e)}

    def check_payment_status(self, reference_id):
        url = f'{self.BASE_URL}/collection/v1_0/requesttopay/{reference_id}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Target-Environment': self.environment,
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'payment_status': data.get('status'),
                    'financial_transaction_id': data.get('financialTransactionId'),
                    'reason': data.get('reason')
                }
            return {'status': 'error', 'message': 'Erreur lors de la vérification'}
        except requests.RequestException as e:
            return {'status': 'error', 'message': str(e)}


class MTNMoMoSimulator:
    """Simulateur MTN MoMo pour le développement"""

    @staticmethod
    def request_to_pay(amount, phone_number, external_id, payer_message='Paiement TSI', payee_note='TSI Payment'):
        reference_id = f'TSI-SIM-{external_id[:8]}'
        return {
            'status': 'success',
            'reference_id': reference_id,
            'message': 'Simulation: En production, une requête USSD serait envoyée au téléphone',
            'simulated': True
        }

    @staticmethod
    def check_payment_status(reference_id):
        return {
            'status': 'success',
            'payment_status': 'SUCCESSFUL',
            'financial_transaction_id': f'FIN-{reference_id[:12]}',
            'simulated': True
        }
