from flask import request, render_template, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
import sqlite3
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re
import logging
import os
from security_improvements import SecurityManager
from subscription_system import create_subscription, get_db_connection, SUBSCRIPTION_PLANS
from payment_gateways import WebpayGateway, PayPalGateway

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegistrationWithSubscription:
    def __init__(self, app):
        self.app = app
        self.security_manager = SecurityManager()
        # Usar funciones directas del sistema de suscripciones
        self.webpay_gateway = WebpayGateway()
        self.paypal_gateway = PayPalGateway()
        
    def register_routes(self):
        """Registra las rutas relacionadas con el registro con suscripción"""
        
        @self.app.route('/register-subscription', methods=['GET', 'POST'])
        def register_with_subscription():
            if request.method == 'GET':
                return render_template('register_with_subscription.html')
            
            try:
                # Obtener datos del formulario
                username = request.form.get('username', '').strip()
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirmPassword', '')
                selected_plan = request.form.get('selected_plan', '')
                
                # Datos de tarjeta
                card_number = request.form.get('card_number', '').replace(' ', '')
                expiry_date = request.form.get('expiry_date', '')
                cvv = request.form.get('cvv', '')
                card_name = request.form.get('card_name', '').strip()
                terms = request.form.get('terms')
                
                # Validaciones básicas
                validation_errors = self._validate_registration_data(
                    username, email, password, confirm_password, 
                    selected_plan, card_number, expiry_date, cvv, card_name, terms
                )
                
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'error')
                    return render_template('register_with_subscription.html')
                
                # Verificar si el usuario ya existe
                if self._user_exists(username, email):
                    flash('El nombre de usuario o email ya están registrados', 'error')
                    return render_template('register_with_subscription.html')
                
                # Procesar pago si es necesario
                payment_result = None
                if selected_plan != 'free_trial':
                    payment_result = self._process_payment(selected_plan, card_number, expiry_date, cvv, card_name)
                    if not payment_result['success']:
                        flash(f'Error en el pago: {payment_result["error"]}', 'error')
                        return render_template('register_with_subscription.html')
                
                # Crear usuario y suscripción
                user_result = self._create_user_with_subscription(
                    username, email, password, selected_plan, payment_result
                )
                
                if user_result:
                    # Enviar email de verificación
                    self._send_verification_email(email, username, user_result['verification_token'])
                    
                    flash('¡Registro exitoso! Se ha enviado un email de verificación a tu correo.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Error al crear la cuenta. Inténtalo nuevamente.', 'error')
                    return render_template('register_with_subscription.html')
                    
            except Exception as e:
                logger.error(f"Error en registro con suscripción: {str(e)}")
                flash('Error interno del servidor. Inténtalo más tarde.', 'error')
                return render_template('register_with_subscription.html')
        
        @self.app.route('/api/validate-card', methods=['POST'])
        def validate_card():
            """API endpoint para validar datos de tarjeta en tiempo real"""
            try:
                data = request.get_json()
                card_number = data.get('card_number', '').replace(' ', '')
                expiry_date = data.get('expiry_date', '')
                cvv = data.get('cvv', '')
                
                validation_result = self._validate_card_data(card_number, expiry_date, cvv)
                return jsonify(validation_result)
                
            except Exception as e:
                logger.error(f"Error validando tarjeta: {str(e)}")
                return jsonify({'valid': False, 'error': 'Error de validación'})
    
    def _validate_registration_data(self, username, email, password, confirm_password, 
                                  selected_plan, card_number, expiry_date, cvv, card_name, terms):
        """Valida todos los datos del formulario de registro"""
        errors = []
        
        # Validar datos básicos
        if not username or len(username) < 3:
            errors.append('El nombre de usuario debe tener al menos 3 caracteres')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('El nombre de usuario solo puede contener letras, números y guiones bajos')
        
        # Validar email
        email_validation = self.security_manager.validate_email(email)
        if email_validation != 0:
            errors.append('El formato del email no es válido')
        
        # Validar contraseña
        password_validation = self.security_manager.validate_password_strength(password)
        if password_validation != 0:
            errors.append('La contraseña no cumple con los requisitos de seguridad')
        
        if password != confirm_password:
            errors.append('Las contraseñas no coinciden')
        
        # Validar plan seleccionado
        valid_plans = ['free_trial', 'standard', 'pro']
        if selected_plan not in valid_plans:
            errors.append('Debes seleccionar un plan válido')
        
        # Validar datos de tarjeta
        card_validation = self._validate_card_data(card_number, expiry_date, cvv)
        if not card_validation['valid']:
            errors.append(f'Datos de tarjeta inválidos: {card_validation.get("error", "Error desconocido")}')
        
        if not card_name or len(card_name.strip()) < 2:
            errors.append('El nombre en la tarjeta es requerido')
        
        # Validar términos y condiciones
        if not terms:
            errors.append('Debes aceptar los términos y condiciones')
        
        return errors
    
    def _validate_card_data(self, card_number, expiry_date, cvv):
        """Valida los datos de la tarjeta de crédito"""
        try:
            # Validar número de tarjeta (algoritmo de Luhn)
            if not self._luhn_check(card_number):
                return {'valid': False, 'error': 'Número de tarjeta inválido'}
            
            # Validar fecha de expiración
            if not re.match(r'^\d{2}/\d{2}$', expiry_date):
                return {'valid': False, 'error': 'Formato de fecha inválido (MM/AA)'}
            
            month, year = expiry_date.split('/')
            month, year = int(month), int('20' + year)
            
            if month < 1 or month > 12:
                return {'valid': False, 'error': 'Mes inválido'}
            
            current_date = datetime.now()
            expiry_date_obj = datetime(year, month, 1)
            
            if expiry_date_obj < current_date:
                return {'valid': False, 'error': 'Tarjeta expirada'}
            
            # Validar CVV
            if not re.match(r'^\d{3,4}$', cvv):
                return {'valid': False, 'error': 'CVV inválido'}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validando tarjeta: {str(e)}")
            return {'valid': False, 'error': 'Error de validación'}
    
    def _luhn_check(self, card_number):
        """Implementa el algoritmo de Luhn para validar números de tarjeta"""
        try:
            # Remover espacios y convertir a string
            card_number = str(card_number).replace(' ', '')
            
            # Verificar que solo contenga dígitos
            if not card_number.isdigit():
                return False
            
            # Verificar longitud (13-19 dígitos)
            if len(card_number) < 13 or len(card_number) > 19:
                return False
            
            # Algoritmo de Luhn
            total = 0
            reverse_digits = card_number[::-1]
            
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:  # Cada segundo dígito desde la derecha
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                total += n
            
            return total % 10 == 0
            
        except Exception:
            return False
    
    def _user_exists(self, username, email):
        """Verifica si el usuario ya existe"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error verificando usuario existente: {str(e)}")
            return True  # En caso de error, asumir que existe para evitar duplicados
    
    def _process_payment(self, plan_type, card_number, expiry_date, cvv, card_name):
        """Procesa el pago según el plan seleccionado"""
        try:
            # Definir precios
            prices = {
                'standard': 9990,  # CLP
                'pro': 19990      # CLP
            }
            
            if plan_type not in prices:
                return {'success': False, 'error': 'Plan inválido'}
            
            amount = prices[plan_type]
            
            # Por ahora, simular el pago exitoso
            # En producción, aquí se integraría con el gateway real
            payment_result = {
                'success': True,
                'transaction_id': f'TXN_{secrets.token_hex(8).upper()}',
                'amount': amount,
                'currency': 'CLP',
                'payment_method': 'credit_card',
                'card_last_four': card_number[-4:] if len(card_number) >= 4 else '****'
            }
            
            logger.info(f"Pago procesado: {payment_result['transaction_id']} por ${amount} CLP")
            return payment_result
            
        except Exception as e:
            logger.error(f"Error procesando pago: {str(e)}")
            return {'success': False, 'error': 'Error procesando el pago'}
    
    def _create_user_with_subscription(self, username, email, password, plan_type, payment_result):
        """Crea el usuario y su suscripción en la base de datos"""
        try:
            # Usar la conexión de PostgreSQL del sistema principal
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hash de la contraseña
            password_hash = generate_password_hash(password)
            
            # Token de verificación
            verification_token = secrets.token_urlsafe(32)
            
            # Crear usuario
            cursor.execute("""
                INSERT INTO users (
                    username, email, password_hash, verification_token, 
                    created_at, current_plan, subscription_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                username, email, password_hash, verification_token,
                datetime.now().isoformat(), plan_type, 'active'
            ))
            
            user_id = cursor.fetchone()['id']
            
            # Crear suscripción
            start_date = datetime.now()
            
            # Calcular fecha de fin según el plan
            if plan_type == 'free_trial':
                end_date = start_date + timedelta(days=7)
                price = 0
            elif plan_type == 'standard':
                end_date = start_date + timedelta(days=30)
                price = 9990
            elif plan_type == 'pro':
                end_date = start_date + timedelta(days=30)
                price = 19990
            
            cursor.execute("""
                INSERT INTO subscriptions (
                    user_id, plan_type, start_date, end_date, 
                    status, amount, payment_method, transaction_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                user_id, plan_type, start_date.isoformat(), end_date.isoformat(),
                'active', price, 'credit_card' if payment_result else 'free',
                payment_result['transaction_id'] if payment_result else None
            ))
            
            subscription_id = cursor.fetchone()['id']
            
            # Registrar el pago si existe
            if payment_result:
                cursor.execute("""
                    INSERT INTO payments (
                        user_id, subscription_id, amount, currency, 
                        payment_method, transaction_id, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, subscription_id, payment_result['amount'], 
                    payment_result['currency'], payment_result['payment_method'],
                    payment_result['transaction_id'], 'completed', 
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Usuario creado exitosamente: {username} con plan {plan_type}")
            return {'user_id': user_id, 'verification_token': verification_token}
            
        except Exception as e:
            logger.error(f"Error creando usuario con suscripción: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return None
    
    def _send_verification_email(self, email, username, verification_token=None):
        """Envía email de verificación al usuario"""
        try:
            # Configuración del email desde variables de entorno
            import os
            smtp_server = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('EMAIL_PORT', 587))
            sender_email = os.getenv('EMAIL_USER')
            sender_password = os.getenv('EMAIL_PASSWORD')
            
            # Verificar que las credenciales estén configuradas
            if not sender_email or not sender_password:
                logger.error("Credenciales de email no configuradas")
                return False
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = "¡Bienvenido a ARMind CVs! Verifica tu cuenta"
            message["From"] = sender_email
            message["To"] = email
            
            # Contenido del email
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #007bff;">¡Bienvenido a ARMind CVs, {username}!</h2>
                        
                        <p>Gracias por registrarte en nuestra plataforma. Tu cuenta ha sido creada exitosamente.</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Próximos pasos:</h3>
                            <ol>
                                <li>Verifica tu email haciendo clic en el enlace de abajo</li>
                                <li>Completa tu perfil</li>
                                <li>¡Comienza a crear CVs profesionales!</li>
                            </ol>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:5000/verify_email/{verification_token}" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Verificar Email
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px;">
                            Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                            <a href="http://localhost:5000/verify_email/{verification_token}">http://localhost:5000/verify_email/{verification_token}</a>
                        </p>
                        
                        <p style="color: #666; font-size: 14px;">
                            Si no solicitaste esta cuenta, puedes ignorar este email.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #666; font-size: 12px; text-align: center;">
                            © 2024 ARMind CVs. Todos los derechos reservados.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            part = MIMEText(html_content, "html")
            message.attach(part)
            
            # Enviar email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            server.quit()
            
            logger.info(f"Email de verificación enviado a {email}")
            
        except Exception as e:
            logger.error(f"Error enviando email de verificación: {str(e)}")