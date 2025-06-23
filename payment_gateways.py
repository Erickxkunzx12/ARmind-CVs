import os
import requests
import json
from datetime import datetime
import hashlib
import hmac
import base64
from dotenv import load_dotenv
from subscription_system import create_subscription, get_db_connection

# Cargar variables de entorno
load_dotenv()

class WebpayGateway:
    """Integración con Webpay Plus de Transbank"""
    
    def __init__(self):
        self.api_key = os.getenv('WEBPAY_API_KEY')
        self.commerce_code = os.getenv('WEBPAY_COMMERCE_CODE')
        self.environment = os.getenv('WEBPAY_ENVIRONMENT', 'integration')  # 'integration' o 'production'
        
        if self.environment == 'production':
            self.base_url = 'https://webpay3g.transbank.cl'
        else:
            self.base_url = 'https://webpay3gint.transbank.cl'
    
    def create_transaction(self, amount, order_id, return_url):
        """Crear una transacción en Webpay"""
        try:
            url = f"{self.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions"
            
            headers = {
                'Tbk-Api-Key-Id': self.commerce_code,
                'Tbk-Api-Key-Secret': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'buy_order': str(order_id),
                'session_id': f"session_{order_id}",
                'amount': int(amount),
                'return_url': return_url
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error en Webpay: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al crear transacción Webpay: {e}")
            return None
    
    def confirm_transaction(self, token):
        """Confirmar una transacción en Webpay"""
        try:
            url = f"{self.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions/{token}"
            
            headers = {
                'Tbk-Api-Key-Id': self.commerce_code,
                'Tbk-Api-Key-Secret': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.put(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error al confirmar transacción Webpay: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al confirmar transacción Webpay: {e}")
            return None

class PayPalGateway:
    """Integración con PayPal"""
    
    def __init__(self):
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.environment = os.getenv('PAYPAL_ENVIRONMENT', 'sandbox')  # 'sandbox' o 'live'
        
        if self.environment == 'live':
            self.base_url = 'https://api.paypal.com'
        else:
            self.base_url = 'https://api.sandbox.paypal.com'
    
    def get_access_token(self):
        """Obtener token de acceso de PayPal"""
        try:
            url = f"{self.base_url}/v1/oauth2/token"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            auth = (self.client_id, self.client_secret)
            data = 'grant_type=client_credentials'
            
            response = requests.post(url, headers=headers, data=data, auth=auth)
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                print(f"Error al obtener token PayPal: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al obtener token PayPal: {e}")
            return None
    
    def create_payment(self, amount, currency, description, return_url, cancel_url):
        """Crear un pago en PayPal"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            url = f"{self.base_url}/v1/payments/payment"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            # Convertir CLP a USD para PayPal (aproximación)
            if currency == 'CLP':
                usd_amount = round(float(amount) / 800, 2)  # Tasa aproximada
                currency = 'USD'
            else:
                usd_amount = amount
            
            data = {
                'intent': 'sale',
                'payer': {
                    'payment_method': 'paypal'
                },
                'transactions': [{
                    'amount': {
                        'total': str(usd_amount),
                        'currency': currency
                    },
                    'description': description
                }],
                'redirect_urls': {
                    'return_url': return_url,
                    'cancel_url': cancel_url
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error al crear pago PayPal: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al crear pago PayPal: {e}")
            return None
    
    def execute_payment(self, payment_id, payer_id):
        """Ejecutar un pago en PayPal"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            url = f"{self.base_url}/v1/payments/payment/{payment_id}/execute"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            data = {
                'payer_id': payer_id
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error al ejecutar pago PayPal: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error al ejecutar pago PayPal: {e}")
            return None

def save_payment_transaction(user_id, subscription_id, gateway, transaction_id, amount, currency, status, gateway_response=None):
    """Guardar transacción de pago en la base de datos"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO payment_transactions (user_id, subscription_id, payment_gateway, transaction_id, amount, currency, status, gateway_response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, subscription_id, gateway, transaction_id, amount, currency, status, json.dumps(gateway_response) if gateway_response else None))
        
        transaction_db_id = cursor.fetchone()['id']
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return transaction_db_id
        
    except Exception as e:
        print(f"Error al guardar transacción: {e}")
        connection.rollback()
        return False

def process_payment_success(user_id, plan_type, gateway, transaction_id, gateway_response):
    """Procesar un pago exitoso y crear la suscripción"""
    try:
        # Crear la suscripción
        subscription_id = create_subscription(user_id, plan_type, gateway, transaction_id)
        
        if subscription_id:
            # Guardar la transacción
            save_payment_transaction(
                user_id=user_id,
                subscription_id=subscription_id,
                gateway=gateway,
                transaction_id=transaction_id,
                amount=gateway_response.get('amount', 0),
                currency=gateway_response.get('currency', 'CLP'),
                status='completed',
                gateway_response=gateway_response
            )
            
            print(f"✅ Pago procesado exitosamente para usuario {user_id}")
            return True
        else:
            print(f"❌ Error al crear suscripción para usuario {user_id}")
            return False
            
    except Exception as e:
        print(f"Error al procesar pago exitoso: {e}")
        return False

def get_payment_gateway(gateway_type):
    """Factory para obtener la pasarela de pago correspondiente"""
    if gateway_type == 'webpay':
        return WebpayGateway()
    elif gateway_type == 'paypal':
        return PayPalGateway()
    else:
        raise ValueError(f"Pasarela de pago no soportada: {gateway_type}")

# Configuración de ejemplo para variables de entorno
if __name__ == "__main__":
    print("Configuración requerida en .env:")
    print("")
    print("# Webpay (Transbank)")
    print("WEBPAY_API_KEY=tu_api_key_aqui")
    print("WEBPAY_COMMERCE_CODE=tu_commerce_code_aqui")
    print("WEBPAY_ENVIRONMENT=integration  # o 'production'")
    print("")
    print("# PayPal")
    print("PAYPAL_CLIENT_ID=tu_client_id_aqui")
    print("PAYPAL_CLIENT_SECRET=tu_client_secret_aqui")
    print("PAYPAL_ENVIRONMENT=sandbox  # o 'live'")