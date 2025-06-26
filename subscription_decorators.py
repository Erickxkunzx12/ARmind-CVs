
# Decorador para verificar restricciones de suscripción
from functools import wraps
from flask import session, flash, redirect, url_for
from subscription_system import check_user_limits, increment_usage

def require_subscription_limit(action_type, increment_on_success=False):
    """Decorador para verificar límites de suscripción"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                flash('Debes iniciar sesión', 'error')
                return redirect(url_for('login'))
            
            # Verificar límites
            can_perform, message = check_user_limits(user_id, action_type)
            if not can_perform:
                flash(f'Restricción de plan: {message}', 'error')
                return redirect(url_for('dashboard'))
            
            # Ejecutar la función original
            result = f(*args, **kwargs)
            
            # Incrementar uso si es exitoso
            if increment_on_success and result:
                increment_usage(user_id, action_type)
            
            return result
        return decorated_function
    return decorator
