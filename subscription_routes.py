from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from subscription_system import (
    SUBSCRIPTION_PLANS, get_user_subscription, 
    check_user_limits, increment_usage, create_subscription
)
from subscription_helpers import get_complete_user_usage
from payment_gateways import (
    get_payment_gateway, save_payment_transaction, process_payment_success
)
import uuid
from datetime import datetime

# Crear blueprint para las rutas de suscripción
subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/plans')
def view_plans():
    """Mostrar los planes de suscripción disponibles"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_subscription = get_user_subscription(session['user_id'])
    user_usage = get_complete_user_usage(session['user_id'])
    
    return render_template('subscription_plans.html', 
                         subscription_plans=SUBSCRIPTION_PLANS,
                         user_subscription=user_subscription,
                         user_usage=user_usage)

@subscription_bp.route('/subscribe/<plan_type>')
def subscribe(plan_type):
    """Iniciar proceso de suscripción"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if plan_type not in SUBSCRIPTION_PLANS:
        flash('Plan de suscripción no válido', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    plan = SUBSCRIPTION_PLANS[plan_type]
    
    # Si es plan gratuito, crear suscripción directamente
    if plan_type == 'free_trial':
        subscription_id = create_subscription(session['user_id'], plan_type, 'free', 'free_trial')
        if subscription_id:
            flash('¡Plan gratuito activado exitosamente!', 'success')
        else:
            flash('Error al activar el plan gratuito', 'error')
        return redirect(url_for('dashboard'))
    
    # Para planes pagos, mostrar opciones de pago
    return render_template('payment_options.html', 
                         plan=plan, 
                         plan_type=plan_type)

@subscription_bp.route('/payment/<plan_type>/<gateway>')
def initiate_payment(plan_type, gateway):
    """Iniciar proceso de pago"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if plan_type not in SUBSCRIPTION_PLANS or gateway not in ['webpay', 'paypal']:
        flash('Parámetros de pago no válidos', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    plan = SUBSCRIPTION_PLANS[plan_type]
    amount = plan['price']
    
    # Generar ID único para la orden
    order_id = f"{session['user_id']}_{plan_type}_{int(datetime.now().timestamp())}"
    
    try:
        payment_gateway = get_payment_gateway(gateway)
        
        if gateway == 'webpay':
            # URLs de retorno para Webpay
            return_url = url_for('subscription.webpay_return', _external=True)
            
            transaction = payment_gateway.create_transaction(
                amount=amount,
                order_id=order_id,
                return_url=return_url
            )
            
            if transaction and 'url' in transaction:
                # Guardar información de la transacción en sesión
                session['pending_payment'] = {
                    'plan_type': plan_type,
                    'gateway': gateway,
                    'order_id': order_id,
                    'token': transaction.get('token')
                }
                return redirect(transaction['url'])
            else:
                flash('Error al iniciar el pago con Webpay', 'error')
                
        elif gateway == 'paypal':
            # URLs de retorno para PayPal
            return_url = url_for('subscription.paypal_return', _external=True)
            cancel_url = url_for('subscription.paypal_cancel', _external=True)
            
            payment = payment_gateway.create_payment(
                amount=amount,
                currency='CLP',
                description=f"Suscripción {plan['name']} - ARMIND",
                return_url=return_url,
                cancel_url=cancel_url
            )
            
            if payment and 'links' in payment:
                # Buscar URL de aprobación
                approval_url = None
                for link in payment['links']:
                    if link['rel'] == 'approval_url':
                        approval_url = link['href']
                        break
                
                if approval_url:
                    # Guardar información de la transacción en sesión
                    session['pending_payment'] = {
                        'plan_type': plan_type,
                        'gateway': gateway,
                        'order_id': order_id,
                        'payment_id': payment['id']
                    }
                    return redirect(approval_url)
                else:
                    flash('Error al obtener URL de pago de PayPal', 'error')
            else:
                flash('Error al iniciar el pago con PayPal', 'error')
    
    except Exception as e:
        print(f"Error al iniciar pago: {e}")
        flash('Error interno al procesar el pago', 'error')
    
    return redirect(url_for('subscription.view_plans'))

@subscription_bp.route('/webpay/return')
def webpay_return():
    """Manejar retorno de Webpay"""
    if 'user_id' not in session or 'pending_payment' not in session:
        flash('Sesión de pago no válida', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    token_ws = request.args.get('token_ws')
    pending_payment = session['pending_payment']
    
    if not token_ws or token_ws != pending_payment.get('token'):
        flash('Token de pago no válido', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    try:
        payment_gateway = get_payment_gateway('webpay')
        result = payment_gateway.confirm_transaction(token_ws)
        
        if result and result.get('status') == 'AUTHORIZED':
            # Pago exitoso
            success = process_payment_success(
                user_id=session['user_id'],
                plan_type=pending_payment['plan_type'],
                gateway='webpay',
                transaction_id=result.get('buy_order'),
                gateway_response=result
            )
            
            if success:
                flash('¡Pago procesado exitosamente! Tu suscripción ha sido activada.', 'success')
            else:
                flash('Error al activar la suscripción. Contacta al soporte.', 'error')
        else:
            flash('El pago no fue autorizado', 'error')
    
    except Exception as e:
        print(f"Error al confirmar pago Webpay: {e}")
        flash('Error al procesar el pago', 'error')
    
    # Limpiar sesión
    session.pop('pending_payment', None)
    return redirect(url_for('dashboard'))

@subscription_bp.route('/paypal/return')
def paypal_return():
    """Manejar retorno exitoso de PayPal"""
    if 'user_id' not in session or 'pending_payment' not in session:
        flash('Sesión de pago no válida', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    pending_payment = session['pending_payment']
    
    if not payment_id or payment_id != pending_payment.get('payment_id'):
        flash('ID de pago no válido', 'error')
        return redirect(url_for('subscription.view_plans'))
    
    try:
        payment_gateway = get_payment_gateway('paypal')
        result = payment_gateway.execute_payment(payment_id, payer_id)
        
        if result and result.get('state') == 'approved':
            # Pago exitoso
            success = process_payment_success(
                user_id=session['user_id'],
                plan_type=pending_payment['plan_type'],
                gateway='paypal',
                transaction_id=payment_id,
                gateway_response=result
            )
            
            if success:
                flash('¡Pago procesado exitosamente! Tu suscripción ha sido activada.', 'success')
            else:
                flash('Error al activar la suscripción. Contacta al soporte.', 'error')
        else:
            flash('El pago no fue aprobado', 'error')
    
    except Exception as e:
        print(f"Error al ejecutar pago PayPal: {e}")
        flash('Error al procesar el pago', 'error')
    
    # Limpiar sesión
    session.pop('pending_payment', None)
    return redirect(url_for('dashboard'))

@subscription_bp.route('/paypal/cancel')
def paypal_cancel():
    """Manejar cancelación de PayPal"""
    flash('Pago cancelado por el usuario', 'info')
    session.pop('pending_payment', None)
    return redirect(url_for('subscription.view_plans'))

@subscription_bp.route('/usage/check')
def check_usage():
    """API para verificar límites de uso"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    resource_type = request.args.get('type')  # 'cv_analysis' o 'cv_creation'
    
    if not resource_type:
        return jsonify({'error': 'Tipo de recurso requerido'}), 400
    
    can_use, remaining = check_user_limits(session['user_id'], resource_type)
    
    return jsonify({
        'can_use': can_use,
        'remaining': remaining,
        'user_id': session['user_id']
    })

@subscription_bp.route('/usage/increment', methods=['POST'])
def increment_user_usage():
    """API para incrementar el uso de recursos"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    resource_type = data.get('type')  # 'cv_analysis' o 'cv_creation'
    
    if not resource_type:
        return jsonify({'error': 'Tipo de recurso requerido'}), 400
    
    success = increment_usage(session['user_id'], resource_type)
    
    return jsonify({
        'success': success,
        'user_id': session['user_id']
    })

@subscription_bp.route('/my-subscription')
def my_subscription():
    """Ver detalles de la suscripción actual"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_subscription = get_user_subscription(session['user_id'])
    user_usage = get_complete_user_usage(session['user_id'])
    
    return render_template('my_subscription.html',
                         user_subscription=user_subscription,
                         user_usage=user_usage,
                         subscription_plans=SUBSCRIPTION_PLANS)