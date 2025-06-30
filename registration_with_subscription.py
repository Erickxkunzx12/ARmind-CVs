from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
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
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                username = request.form.get('username', '').strip()
                country_code = request.form.get('country_code', '+56').strip()
                phone = request.form.get('phone', '').strip()
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirmPassword', '')
                selected_plan = request.form.get('selected_plan', '')
                
                # Combinar código de país con número de teléfono
                full_phone = f"{country_code}{phone}" if phone else ''
                
                # Método de pago seleccionado
                payment_method = request.form.get('payment_method', '')
                terms = request.form.get('terms')
                
                # Validaciones básicas
                validation_errors = self._validate_registration_data(
                    username, email, password, confirm_password, 
                    selected_plan, payment_method, terms
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
                    # Crear usuario primero para obtener el ID
                    temp_user_result = self._create_temp_user(
                        username, first_name, last_name, full_phone, email, password
                    )
                    
                    if not temp_user_result:
                        flash('Error al crear la cuenta. Inténtalo nuevamente.', 'error')
                        return render_template('register_with_subscription.html')
                    
                    # Redirigir a la pasarela de pago
                    payment_url = self._initiate_payment(selected_plan, payment_method, temp_user_result['user_id'])
                    if payment_url:
                        return redirect(payment_url)
                    else:
                        flash('Error al inicializar el pago. Inténtalo nuevamente.', 'error')
                        return render_template('register_with_subscription.html')
                
                # Crear usuario y suscripción
                user_result = self._create_user_with_subscription(
                    username, first_name, last_name, full_phone, email, password, selected_plan, payment_result
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
        
        @self.app.route('/payment/success/<int:user_id>', methods=['GET', 'POST'])
        def payment_success(user_id):
            """Maneja el retorno exitoso de la pasarela de pago"""
            try:
                # Verificar y confirmar el pago
                payment_confirmed = self._confirm_payment(request)
                
                if payment_confirmed:
                    # Activar la suscripción del usuario
                    success = self._activate_user_subscription(user_id, payment_confirmed)
                    
                    if success:
                        # Enviar email de verificación
                        user_data = self._get_user_data(user_id)
                        if user_data:
                            self._send_verification_email(
                                user_data['email'], 
                                user_data['username'], 
                                user_data['verification_token']
                            )
                        
                        flash('¡Pago exitoso! Se ha enviado un email de verificación a tu correo.', 'success')
                        return redirect(url_for('login'))
                    else:
                        flash('Error al activar la suscripción. Contacta soporte.', 'error')
                        return redirect(url_for('register_with_subscription'))
                else:
                    flash('Error en la verificación del pago. Inténtalo nuevamente.', 'error')
                    return redirect(url_for('register_with_subscription'))
                    
            except Exception as e:
                logger.error(f"Error procesando pago exitoso: {str(e)}")
                flash('Error procesando el pago. Contacta soporte.', 'error')
                return redirect(url_for('register_with_subscription'))
        
        @self.app.route('/payment/cancel/<int:user_id>', methods=['GET'])
        def payment_cancel(user_id):
            """Maneja la cancelación del pago"""
            try:
                # Eliminar usuario temporal
                self._delete_temp_user(user_id)
                flash('Pago cancelado. Puedes intentar nuevamente.', 'warning')
                return redirect(url_for('register_with_subscription'))
                
            except Exception as e:
                logger.error(f"Error manejando cancelación: {str(e)}")
                flash('Error procesando la cancelación.', 'error')
                return redirect(url_for('register_with_subscription'))
    
    def _validate_registration_data(self, username, email, password, confirm_password, 
                                  selected_plan, payment_method, terms):
        """Valida todos los datos del formulario de registro"""
        errors = []
        
        # Validar datos básicos
        if not username or len(username) < 3:
            errors.append('El nombre de usuario debe tener al menos 3 caracteres')
        
        if len(username) > 30:
            errors.append('El nombre de usuario no puede tener más de 30 caracteres')
        
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            errors.append('El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos')
        
        # Verificar que el username no esté ya en uso
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                errors.append('Este nombre de usuario ya está en uso')
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error verificando username: {str(e)}")
            errors.append('Error verificando disponibilidad del nombre de usuario')
        
        # Validar email
        if not self.security_manager.validate_email(email):
            errors.append('El formato del email no es válido')
        
        # Validar contraseña
        password_errors = self.security_manager.validate_password_strength(password)
        if password_errors:
            errors.extend(password_errors)
        
        if password != confirm_password:
            errors.append('Las contraseñas no coinciden')
        
        # Validar plan seleccionado
        valid_plans = ['free_trial', 'standard', 'pro']
        if selected_plan not in valid_plans:
            errors.append('Debes seleccionar un plan válido')
        
        # Validar método de pago (solo para planes pagos)
        if selected_plan != 'free_trial':
            valid_payment_methods = ['webpay', 'paypal']
            if payment_method not in valid_payment_methods:
                errors.append('Debes seleccionar un método de pago válido')
        
        # Validar términos y condiciones
        if not terms:
            errors.append('Debes aceptar los términos y condiciones')
        
        return errors
    
    def _create_temp_user(self, username, first_name, last_name, phone, email, password):
        """Crea un usuario temporal para el proceso de pago"""
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            verification_token = secrets.token_urlsafe(32)
            
            cursor.execute("""
                INSERT INTO users (
                    username, first_name, last_name, phone, email, password_hash, verification_token, 
                    created_at, current_plan, subscription_status, is_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                username, first_name, last_name, phone, email, password_hash, verification_token,
                datetime.now().isoformat(), 'pending', 'pending', False
            ))
            
            user_id = cursor.fetchone()['id']
            conn.commit()
            conn.close()
            
            return {
                'user_id': user_id,
                'verification_token': verification_token
            }
            
        except Exception as e:
            logger.error(f"Error creando usuario temporal: {str(e)}")
            return None
    
    def _initiate_payment(self, plan_type, payment_method, user_id):
        """Inicia el proceso de pago con la pasarela seleccionada"""
        try:
            # Definir precios
            prices = {
                'standard': 9990,  # CLP
                'pro': 19990      # CLP
            }
            
            if plan_type not in prices:
                return None
            
            amount = prices[plan_type]
            
            # URLs de retorno
            return_url = f"{request.url_root}payment/success/{user_id}"
            cancel_url = f"{request.url_root}payment/cancel/{user_id}"
            
            if payment_method == 'webpay':
                # Inicializar transacción con WebPay
                payment_url = self.webpay_gateway.create_transaction(
                    amount=amount,
                    order_id=f"ORDER_{user_id}_{secrets.token_hex(4).upper()}",
                    return_url=return_url
                )
                return payment_url
                
            elif payment_method == 'paypal':
                # Inicializar transacción con PayPal
                payment_url = self.paypal_gateway.create_payment(
                    amount=amount,
                    currency='USD',  # PayPal usa USD
                    description=f"Suscripción {plan_type.title()} - ARMIND",
                    return_url=return_url,
                    cancel_url=cancel_url
                )
                return payment_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error iniciando pago: {str(e)}")
            return None
    
    def _confirm_payment(self, request_obj):
        """Confirma el pago con la pasarela correspondiente"""
        try:
            # Determinar qué pasarela procesó el pago basado en los parámetros
            if 'token_ws' in request_obj.args:  # WebPay
                token = request_obj.args.get('token_ws')
                return self.webpay_gateway.confirm_transaction(token)
            elif 'paymentId' in request_obj.args:  # PayPal
                payment_id = request_obj.args.get('paymentId')
                payer_id = request_obj.args.get('PayerID')
                return self.paypal_gateway.execute_payment(payment_id, payer_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error confirmando pago: {str(e)}")
            return None
    
    def _activate_user_subscription(self, user_id, payment_data):
        """Activa la suscripción del usuario después del pago exitoso"""
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener datos del usuario
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False
            
            # Determinar el plan basado en el monto pagado
            amount = payment_data.get('amount', 0)
            if amount >= 19990:
                plan_type = 'pro'
            elif amount >= 9990:
                plan_type = 'standard'
            else:
                plan_type = 'free_trial'
            
            # Actualizar usuario
            cursor.execute("""
                UPDATE users 
                SET current_plan = %s, subscription_status = 'active'
                WHERE id = %s
            """, (plan_type, user_id))
            
            # Crear suscripción
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            
            cursor.execute("""
                INSERT INTO subscriptions (
                    user_id, plan_type, start_date, end_date, status, 
                    payment_method, transaction_id, amount
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, plan_type, start_date.isoformat(), end_date.isoformat(),
                'active', payment_data.get('payment_method', 'unknown'),
                payment_data.get('transaction_id', ''), amount
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error activando suscripción: {str(e)}")
            return False
    
    def _get_user_data(self, user_id):
        """Obtiene los datos del usuario"""
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, email, verification_token 
                FROM users WHERE id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de usuario: {str(e)}")
            return None
    
    def _delete_temp_user(self, user_id):
        """Elimina un usuario temporal"""
        try:
            from app import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM users WHERE id = %s AND subscription_status = 'pending'", (user_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error eliminando usuario temporal: {str(e)}")
     
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
            from app import get_db_connection
            conn = get_db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos")
                return True  # En caso de error, asumir que existe para evitar duplicados
            
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
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
    
    def _create_user_with_subscription(self, username, first_name, last_name, phone, email, password, plan_type, payment_result):
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
                    username, first_name, last_name, phone, email, password_hash, verification_token, 
                    created_at, current_plan, subscription_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                username, first_name, last_name, phone, email, password_hash, verification_token,
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