from subscription_system import get_user_usage, get_user_subscription, SUBSCRIPTION_PLANS
from datetime import datetime

def get_complete_user_usage(user_id):
    """Obtener el uso completo del usuario para todas las funciones"""
    try:
        # Obtener uso de análisis de CV
        cv_analysis_count = get_user_usage(user_id, 'cv_analysis')
        
        # Obtener uso de creación de CV
        cv_creation_count = get_user_usage(user_id, 'cv_creation')
        
        # Retornar objeto con la estructura esperada
        return {
            'cv_analysis_count': cv_analysis_count,
            'cv_creation_count': cv_creation_count,
            'user_id': user_id,
            'last_updated': datetime.now()
        }
    except Exception as e:
        print(f"Error al obtener uso completo del usuario: {e}")
        return {
            'cv_analysis_count': 0,
            'cv_creation_count': 0,
            'user_id': user_id,
            'last_updated': datetime.now()
        }

def get_user_subscription_with_usage(user_id):
    """Obtener suscripción del usuario junto con su uso actual"""
    subscription = get_user_subscription(user_id)
    usage = get_complete_user_usage(user_id)
    
    return {
        'subscription': subscription,
        'usage': usage,
        'plans': SUBSCRIPTION_PLANS
    }