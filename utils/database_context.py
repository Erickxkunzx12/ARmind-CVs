"""Context managers y utilidades para manejo de base de datos"""

from contextlib import contextmanager
from functools import wraps
import logging
from datetime import datetime
from admin_sales_system import get_db_connection
from psycopg2.extras import RealDictCursor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_cursor(dict_cursor=False):
    """Context manager para manejo seguro de conexiones de base de datos"""
    connection = get_db_connection()
    if not connection:
        raise Exception("No se pudo establecer conexión con la base de datos")
    
    cursor = None
    try:
        if dict_cursor:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = connection.cursor()
        
        yield cursor
        connection.commit()
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error en operación de base de datos: {e}")
        raise
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

class DatabaseValidator:
    """Clase para validaciones de base de datos"""
    
    @staticmethod
    def validate_seller_data(data):
        """Validar datos de vendedor"""
        errors = []
        
        if not data.get('name', '').strip():
            errors.append('El nombre del vendedor es requerido')
        
        # Validar email
        email = data.get('email', '').strip()
        if email:
            from security_improvements import SecurityManager
            if not SecurityManager.validate_email(email):
                errors.append('El formato del email es inválido')
        
        commission_rate = data.get('commission_rate')
        if commission_rate is not None:
            try:
                rate = float(commission_rate) * 100  # Convertir a porcentaje
                if rate < 0 or rate > 100:
                    errors.append('La tasa de comisión debe estar entre 0 y 100')
            except (ValueError, TypeError):
                errors.append('La tasa de comisión debe ser un número válido')
        
        return errors
    
    @staticmethod
    def validate_offer_data(data):
        """Validar datos de oferta"""
        errors = []
        
        if not data.get('title', '').strip():
            errors.append('El título de la oferta es requerido')
        
        discount = data.get('discount_percentage')
        if discount is not None:
            try:
                disc = float(discount)
                if disc < 0 or disc > 100:
                    errors.append('El porcentaje de descuento debe estar entre 0 y 100')
            except (ValueError, TypeError):
                errors.append('El porcentaje de descuento debe ser un número válido')
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if end <= start:
                    errors.append('La fecha de fin debe ser posterior a la fecha de inicio')
            except ValueError:
                errors.append('Formato de fecha inválido')
        
        return errors

class AdminLogger:
    """Clase para logging de acciones administrativas"""
    
    @staticmethod
    def log_action(action, user_id, entity_type, entity_id, details=None):
        """Registrar acción administrativa"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{timestamp} - {action} - User: {user_id} - {entity_type}: {entity_id}"
        
        if details:
            message += f" - Details: {details}"
        
        logger.info(message)
        
        # También guardar en base de datos si existe tabla de auditoría
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO admin_audit_log (action, user_id, entity_type, entity_id, details, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (action, user_id, entity_type, entity_id, details, datetime.now()))
        except Exception:
            # Si no existe la tabla de auditoría, solo usar logging
            pass

def validate_admin_data(entity_type):
    """Decorador para validar datos administrativos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, flash, redirect, url_for
            
            if request.method == 'POST':
                data = request.form.to_dict()
                
                if entity_type == 'seller':
                    errors = DatabaseValidator.validate_seller_data(data)
                elif entity_type == 'offer':
                    errors = DatabaseValidator.validate_offer_data(data)
                else:
                    errors = []
                
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return redirect(request.url)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_admin_action(action, entity_type):
    """Decorador para logging de acciones administrativas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session
            
            # Extraer entity_id de los argumentos
            entity_id = None
            if args:
                entity_id = args[0] if isinstance(args[0], int) else None
            
            user_id = session.get('user_id', 'unknown')
            
            try:
                result = f(*args, **kwargs)
                AdminLogger.log_action(action, user_id, entity_type, entity_id, 'SUCCESS')
                return result
            except Exception as e:
                AdminLogger.log_action(action, user_id, entity_type, entity_id, f'ERROR: {str(e)}')
                raise
        
        return decorated_function
    return decorator

class DatabaseService:
    """Servicio base para operaciones de base de datos"""
    
    @staticmethod
    def update_entity(table, entity_id, allowed_fields, **kwargs):
        """Método genérico para actualizar entidades"""
        with get_db_cursor() as cursor:
            # Construir consulta de actualización dinámicamente
            set_clauses = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None and value != '':
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False, "No hay campos válidos para actualizar"
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(entity_id)
            
            query = f"""
                UPDATE {table} 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            
            cursor.execute(query, params)
            
            if cursor.rowcount == 0:
                return False, f"{table.title()} no encontrado"
            
            return True, f"{table.title()} actualizado correctamente"
    
    @staticmethod
    def get_entity_by_id(table, entity_id):
        """Método genérico para obtener entidad por ID"""
        with get_db_cursor(dict_cursor=True) as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE id = %s", (entity_id,))
            return cursor.fetchone()
    
    @staticmethod
    def entity_exists(table, field, value, exclude_id=None):
        """Verificar si una entidad existe"""
        with get_db_cursor() as cursor:
            query = f"SELECT COUNT(*) FROM {table} WHERE {field} = %s"
            params = [value]
            
            if exclude_id:
                query += " AND id != %s"
                params.append(exclude_id)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0] > 0

# Funciones de utilidad mejoradas
def safe_float(value, default=None):
    """Convertir valor a float de forma segura"""
    if value is None or value == '':
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=None):
    """Convertir valor a int de forma segura"""
    if value is None or value == '':
        return default
    
    try:
        return int(float(value))  # Convertir a float primero para manejar "10.5"
    except (ValueError, TypeError):
        return default

def sanitize_string(value, max_length=None):
    """Sanitizar string de entrada"""
    if not value:
        return ''
    
    import re
    
    # Convertir a string y limpiar espacios
    cleaned = str(value).strip()
    
    # Remover caracteres peligrosos
    cleaned = re.sub(r'[<>"\'\/\\]', '', cleaned)
    
    # Limitar longitud si se especifica
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned