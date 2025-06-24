import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

# Definición de planes de suscripción
SUBSCRIPTION_PLANS = {
    'free_trial': {
        'name': 'Free Trial',
        'price': 0,
        'currency': 'CLP',
        'duration_days': 7,
        'max_analyses': 5,
        'max_cvs': 1,
        'limits': {
            'cv_analysis': 5,
            'cv_creation': 1
        },
        'ai_providers': ['openai'],  # Solo OpenAI
        'features': [
            'Análisis básico de CV',
            'Creación de 1 currículum',
            'Acceso por 7 días',
            'Soporte por email'
        ]
    },
    'standard': {
        'name': 'Plan Estándar',
        'price': 10000,
        'currency': 'CLP',
        'duration_days': 30,
        'max_analyses': 10,
        'max_cvs': 5,
        'limits': {
            'cv_analysis': 10,
            'cv_creation': 5
        },
        'ai_providers': ['openai', 'anthropic'],
        'features': [
            'Análisis avanzado de CV',
            'Creación de hasta 5 currículums',
            'Acceso a múltiples IA',
            'Plantillas premium',
            'Soporte prioritario'
        ]
    },
    'pro': {
        'name': 'Plan PRO',
        'price': 20000,
        'currency': 'CLP',
        'duration_days': 30,
        'max_analyses': 20,
        'max_cvs': 10,
        'limits': {
            'cv_analysis': 20,
            'cv_creation': 10
        },
        'ai_providers': ['openai', 'anthropic', 'gemini'],
        'features': [
            'Análisis completo de CV',
            'Creación ilimitada de currículums',
            'Acceso a todas las IA',
            'Plantillas exclusivas',
            'Exportación avanzada',
            'Soporte 24/7',
            'Análisis comparativo'
        ]
    }
}

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
        return connection
    except psycopg2.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def create_subscription_tables():
    """Crear tablas necesarias para el sistema de suscripciones"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Tabla de suscripciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                plan_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NOT NULL,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                amount DECIMAL(10,2),
                currency VARCHAR(10) DEFAULT 'CLP',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de uso de recursos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE,
                resource_type VARCHAR(50) NOT NULL, -- 'analysis' o 'cv_creation'
                used_count INTEGER DEFAULT 0,
                reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de transacciones de pago
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                subscription_id INTEGER REFERENCES subscriptions(id),
                payment_gateway VARCHAR(50) NOT NULL, -- 'webpay' o 'paypal'
                transaction_id VARCHAR(255) UNIQUE NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(10) DEFAULT 'CLP',
                status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
                gateway_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agregar columnas de suscripción a la tabla users si no existen
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS current_plan VARCHAR(50) DEFAULT 'free_trial',
            ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Tablas de suscripción creadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tablas de suscripción: {e}")
        connection.rollback()
        return False

def get_user_subscription(user_id):
    """Obtener la suscripción activa del usuario"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Primero verificar si es administrador
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()
        
        if user_role and user_role[0] == 'admin':
            # Los administradores no necesitan suscripción, tienen acceso completo
            cursor.close()
            connection.close()
            return None
        
        # Para usuarios normales, buscar en la tabla subscriptions
        cursor.execute("""
            SELECT s.*, u.current_plan, u.subscription_status, u.subscription_end_date
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.user_id = %s AND s.status = 'active'
            ORDER BY s.created_at DESC
            LIMIT 1
        """, (user_id,))
        
        subscription = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return subscription
        
    except Exception as e:
        print(f"Error al obtener suscripción del usuario: {e}")
        return None

def get_user_usage(user_id, resource_type):
    """Obtener el uso actual de recursos del usuario"""
    connection = get_db_connection()
    if not connection:
        return 0
    
    try:
        cursor = connection.cursor()
        
        # Verificar si es administrador
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()
        
        if user_role and user_role[0] == 'admin':
            # Los administradores tienen uso ilimitado
            cursor.close()
            connection.close()
            return 0
        
        # Obtener la suscripción activa para usuarios normales
        subscription = get_user_subscription(user_id)
        if not subscription:
            cursor.close()
            connection.close()
            return 0
        
        # Obtener el uso actual del mes
        cursor.execute("""
            SELECT used_count FROM usage_tracking
            WHERE user_id = %s AND resource_type = %s
            AND reset_date >= %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, resource_type, subscription['start_date']))
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return result['used_count'] if result else 0
        
    except Exception as e:
        print(f"Error al obtener uso de recursos: {e}")
        return 0

def check_user_limits(user_id, action_type):
    """Verificar si el usuario puede realizar una acción específica"""
    try:
        # Verificar si es administrador primero
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user_role and user_role[0] == 'admin':
            # Los administradores tienen acceso ilimitado a todo
            return True, "Acceso administrativo completo"
        
        subscription = get_user_subscription(user_id)
        if not subscription:
            return False, "No tienes una suscripción activa"
        
        plan_type = subscription.get('plan_type', subscription.get('current_plan'))
        if plan_type not in SUBSCRIPTION_PLANS:
            return False, "Plan de suscripción no válido"
        
        plan_limits = SUBSCRIPTION_PLANS[plan_type]['limits']
        
        # Verificar límites específicos
        if action_type in plan_limits:
            current_usage = get_user_usage(user_id)
            if current_usage >= plan_limits[action_type]:
                return False, f"Has alcanzado el límite de {plan_limits[action_type]} para {action_type}"
        
        return True, "Acción permitida"
    
    except Exception as e:
        print(f"Error checking user limits: {e}")
        return False, "Error al verificar límites"

def increment_usage(user_id, resource_type):
    """Incrementar el contador de uso de un recurso"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        subscription = get_user_subscription(user_id)
        
        if not subscription:
            return False
        
        # Buscar registro de uso existente
        cursor.execute("""
            SELECT id, used_count FROM usage_tracking
            WHERE user_id = %s AND resource_type = %s
            AND reset_date >= %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, resource_type, subscription['start_date']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar contador existente
            cursor.execute("""
                UPDATE usage_tracking
                SET used_count = used_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (existing['id'],))
        else:
            # Crear nuevo registro
            cursor.execute("""
                INSERT INTO usage_tracking (user_id, subscription_id, resource_type, used_count, reset_date)
                VALUES (%s, %s, %s, 1, %s)
            """, (user_id, subscription['id'], resource_type, subscription['start_date']))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"Error al incrementar uso: {e}")
        connection.rollback()
        return False

def create_subscription(user_id, plan_type, payment_method=None, transaction_id=None):
    """Crear una nueva suscripción para el usuario"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        plan_config = SUBSCRIPTION_PLANS.get(plan_type)
        
        if not plan_config:
            return False
        
        # Calcular fechas
        start_date = datetime.now()
        end_date = start_date + timedelta(days=plan_config['duration_days'])
        
        # Desactivar suscripciones anteriores
        cursor.execute("""
            UPDATE subscriptions
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        
        # Crear nueva suscripción
        cursor.execute("""
            INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, payment_method, transaction_id, amount, currency)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, plan_type, start_date, end_date, payment_method, transaction_id, plan_config['price'], plan_config['currency']))
        
        subscription_id = cursor.fetchone()['id']
        
        # Actualizar información del usuario
        cursor.execute("""
            UPDATE users
            SET current_plan = %s, subscription_status = 'active', subscription_end_date = %s
            WHERE id = %s
        """, (plan_type, end_date, user_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"✅ Suscripción {plan_type} creada para usuario {user_id}")
        return subscription_id
        
    except Exception as e:
        print(f"Error al crear suscripción: {e}")
        connection.rollback()
        return False

if __name__ == "__main__":
    # Crear tablas al ejecutar el script
    create_subscription_tables()