import os
import requests
import json
from datetime import datetime
import hashlib
import hmac
import base64
from dotenv import load_dotenv
from subscription_system import create_subscription, get_db_connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class WebpayGateway:
    """Integración con Webpay Plus de Transbank"""
    
    def __init__(self):
        self.api_key = os.getenv('WEBPAY_API_KEY')
        self.commerce_code = os.getenv('WEBPAY_COMMERCE_CODE')
        self.environment = os.getenv('WEBPAY_ENVIRONMENT', 'integration')  # 'integration' o 'production'
        
        # Validar credenciales
        if not self.api_key or not self.commerce_code:
            logger.warning("Credenciales de Webpay no configuradas. Configurar WEBPAY_API_KEY y WEBPAY_COMMERCE_CODE en .env")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info(f"Webpay configurado en modo: {self.environment}")
        
        if self.environment == 'production':
            self.base_url = 'https://webpay3g.transbank.cl'
        else:
            self.base_url = 'https://webpay3gint.transbank.cl'
    
    def is_available(self):
        """Verificar si el gateway está disponible"""
        return self.is_configured
    
    def create_transaction(self, amount, order_id, return_url):
        """Crear una transacción en Webpay"""
        if not self.is_available():
            logger.error("Webpay no está configurado")
            return {'error': 'Webpay no está configurado correctamente'}
            
        try:
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
            
            logger.info(f"Creando transacción Webpay para orden {order_id} por ${amount}")
            
            response = requests.post(
                f'{self.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Transacción Webpay creada exitosamente: {result.get('token', 'N/A')}")
                return result
            else:
                error_msg = f'Error en Webpay: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return {'error': error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = 'Timeout al conectar con Webpay'
            logger.error(error_msg)
            return {'error': error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = 'Error de conexión con Webpay'
            logger.error(error_msg)
            return {'error': error_msg}
        except Exception as e:
            error_msg = f'Error inesperado en Webpay: {str(e)}'
            logger.error(error_msg)
            return {'error': error_msg}
    
    def confirm_transaction(self, token):
        """Confirmar una transacción en Webpay"""
        if not self.is_available():
            logger.error("Webpay no está configurado")
            return {'error': 'Webpay no está configurado correctamente'}
            
        try:
            headers = {
                'Tbk-Api-Key-Id': self.commerce_code,
                'Tbk-Api-Key-Secret': self.api_key,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Confirmando transacción Webpay con token: {token}")
            
            response = requests.put(
                f'{self.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions/{token}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Transacción Webpay confirmada: {result.get('response_code', 'N/A')}")
                return result
            else:
                error_msg = f'Error al confirmar transacción: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return {'error': error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = 'Timeout al confirmar transacción Webpay'
            logger.error(error_msg)
            return {'error': error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = 'Error de conexión al confirmar Webpay'
            logger.error(error_msg)
            return {'error': error_msg}
        except Exception as e:
            error_msg = f'Error inesperado al confirmar Webpay: {str(e)}'
            logger.error(error_msg)
            return {'error': error_msg}

class PayPalGateway:
    """Integración con PayPal"""
    
    def __init__(self):
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.environment = os.getenv('PAYPAL_ENVIRONMENT', 'sandbox')  # 'sandbox' o 'live'
        
        # Validar credenciales
        if not self.client_id or not self.client_secret:
            logger.warning("Credenciales de PayPal no configuradas. Configurar PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET en .env")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info(f"PayPal configurado en modo: {self.environment}")
        
        if self.environment == 'live':
            self.base_url = 'https://api.paypal.com'
        else:
            self.base_url = 'https://api.sandbox.paypal.com'
    
    def is_available(self):
        """Verificar si el gateway está disponible"""
        return self.is_configured
    
    def get_access_token(self):
        """Obtener token de acceso de PayPal"""
        if not self.is_available():
            logger.error("PayPal no está configurado")
            return None
            
        try:
            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = 'grant_type=client_credentials'
            
            logger.info("Obteniendo token de acceso de PayPal")
            
            response = requests.post(
                f'{self.base_url}/v1/oauth2/token',
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token = response.json()['access_token']
                logger.info("Token de PayPal obtenido exitosamente")
                return token
            else:
                error_msg = f'Error al obtener token PayPal: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            logger.error('Timeout al obtener token de PayPal')
            return None
        except requests.exceptions.ConnectionError:
            logger.error('Error de conexión al obtener token de PayPal')
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener token de PayPal: {e}")
            return None
    
    def create_payment(self, amount_clp, description, return_url, cancel_url):
        """Crear un pago en PayPal (convierte CLP a USD)"""
        if not self.is_available():
            logger.error("PayPal no está configurado")
            return None
            
        access_token = self.get_access_token()
        if not access_token:
            logger.error("No se pudo obtener token de acceso de PayPal")
            return None
            
        try:
            # Convertir CLP a USD (tasa aproximada - en producción usar API de cambio)
            exchange_rate = float(os.getenv('CLP_TO_USD_RATE', '0.00125'))  # Tasa configurable
            amount_usd = round(amount_clp * exchange_rate, 2)
            
            logger.info(f"Creando pago PayPal: ${amount_clp} CLP = ${amount_usd} USD")
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            payment_data = {
                'intent': 'sale',
                'payer': {
                    'payment_method': 'paypal'
                },
                'transactions': [{
                    'amount': {
                        'total': str(amount_usd),
                        'currency': 'USD'
                    },
                    'description': description
                }],
                'redirect_urls': {
                    'return_url': return_url,
                    'cancel_url': cancel_url
                }
            }
            
            response = requests.post(
                f'{self.base_url}/v1/payments/payment',
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Pago PayPal creado exitosamente: {result.get('id', 'N/A')}")
                return result
            else:
                error_msg = f'Error al crear pago PayPal: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            logger.error('Timeout al crear pago PayPal')
            return None
        except requests.exceptions.ConnectionError:
            logger.error('Error de conexión al crear pago PayPal')
            return None
        except Exception as e:
            logger.error(f"Error inesperado al crear pago PayPal: {e}")
            return None
    
    def execute_payment(self, payment_id, payer_id):
        """Ejecutar un pago en PayPal"""
        if not self.is_available():
            logger.error("PayPal no está configurado")
            return None
            
        try:
            access_token = self.get_access_token()
            if not access_token:
                logger.error("No se pudo obtener token de acceso para ejecutar pago")
                return None
                
            logger.info(f"Ejecutando pago PayPal: {payment_id}")
                
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            data = {
                'payer_id': payer_id
            }
            
            response = requests.post(
                f'{self.base_url}/v1/payments/payment/{payment_id}/execute',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Pago PayPal ejecutado exitosamente: {payment_id}")
                return result
            else:
                error_msg = f'Error al ejecutar pago PayPal: {response.status_code} - {response.text}'
                logger.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            logger.error('Timeout al ejecutar pago PayPal')
            return None
        except requests.exceptions.ConnectionError:
            logger.error('Error de conexión al ejecutar pago PayPal')
            return None
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar pago PayPal: {e}")
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
    """Factory function para obtener el gateway de pago apropiado"""
    try:
        if gateway_type == 'webpay':
            gateway = WebpayGateway()
            if not gateway.is_available():
                logger.error("Webpay no está configurado correctamente")
                return None
            return gateway
        elif gateway_type == 'paypal':
            gateway = PayPalGateway()
            if not gateway.is_available():
                logger.error("PayPal no está configurado correctamente")
                return None
            return gateway
        else:
            logger.error(f"Gateway de pago no soportado: {gateway_type}")
            raise ValueError(f"Gateway de pago no soportado: {gateway_type}")
    except Exception as e:
        logger.error(f"Error al inicializar gateway {gateway_type}: {str(e)}")
        return None

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