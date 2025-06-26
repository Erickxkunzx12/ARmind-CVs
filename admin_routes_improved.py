"""Rutas administrativas mejoradas con mejor mantenibilidad"""

from flask import request, render_template, redirect, url_for, flash, session
from functools import wraps
from utils.database_context import (
    get_db_cursor, DatabaseValidator, AdminLogger, 
    validate_admin_data, log_admin_action, DatabaseService,
    safe_float, sanitize_string
)
from admin_sales_system import get_seller_by_id, get_offer_by_id

def admin_required(f):
    """Decorador mejorado para verificar permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'admin':
            flash('No tienes permisos para acceder a esta página', 'error')
            AdminLogger.log_action('UNAUTHORIZED_ACCESS', session.get('user_id'), 'admin_route', request.endpoint)
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

class SellerService:
    """Servicio para manejo de vendedores"""
    
    @staticmethod
    def update(seller_id, data):
        """Actualizar vendedor con validación mejorada"""
        # Validar datos
        errors = DatabaseValidator.validate_seller_data(data)
        if errors:
            return False, '; '.join(errors)
        
        # Verificar si el email ya existe (excluyendo el vendedor actual)
        if data.get('email'):
            if DatabaseService.entity_exists('sellers', 'email', data['email'], exclude_id=seller_id):
                return False, 'Ya existe un vendedor con ese email'
        
        # Preparar datos para actualización
        update_data = {
            'name': sanitize_string(data.get('name'), 255),
            'email': sanitize_string(data.get('email'), 255),
            'phone': sanitize_string(data.get('phone'), 50),
            'commission_rate': safe_float(data.get('commission_rate')),
            'is_active': data.get('is_active', False)
        }
        
        # Filtrar campos vacíos
        update_data = {k: v for k, v in update_data.items() if v is not None and v != ''}
        
        allowed_fields = ['name', 'email', 'phone', 'commission_rate', 'is_active']
        return DatabaseService.update_entity('sellers', seller_id, allowed_fields, **update_data)
    
    @staticmethod
    def get_by_id(seller_id):
        """Obtener vendedor por ID"""
        return DatabaseService.get_entity_by_id('sellers', seller_id)

class OfferService:
    """Servicio para manejo de ofertas"""
    
    @staticmethod
    def update(offer_id, data):
        """Actualizar oferta con validación mejorada"""
        # Validar datos
        errors = DatabaseValidator.validate_offer_data(data)
        if errors:
            return False, '; '.join(errors)
        
        # Preparar datos para actualización
        update_data = {
            'title': sanitize_string(data.get('title'), 255),
            'description': sanitize_string(data.get('description')),
            'discount_percentage': safe_float(data.get('discount_percentage')),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'is_active': data.get('is_active', False),
            'status': sanitize_string(data.get('status', 'active'), 20)
        }
        
        # Filtrar campos vacíos
        update_data = {k: v for k, v in update_data.items() if v is not None and v != ''}
        
        allowed_fields = ['title', 'description', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'status']
        return DatabaseService.update_entity('promotional_offers', offer_id, allowed_fields, **update_data)
    
    @staticmethod
    def get_by_id(offer_id):
        """Obtener oferta por ID"""
        return DatabaseService.get_entity_by_id('promotional_offers', offer_id)

def register_improved_admin_routes(app):
    """Registrar rutas administrativas mejoradas"""
    
    @app.route('/admin/sellers/edit/<int:seller_id>', methods=['GET', 'POST'])
    @admin_required
    @log_admin_action('EDIT_SELLER', 'seller')
    def admin_edit_seller_improved(seller_id):
        """Editar vendedor con validación mejorada"""
        if request.method == 'GET':
            # Mostrar formulario de edición
            seller = SellerService.get_by_id(seller_id)
            if not seller:
                flash('Vendedor no encontrado', 'error')
                return redirect(url_for('admin_sellers'))
            
            AdminLogger.log_action('VIEW_SELLER_EDIT', session.get('user_id'), 'seller', seller_id)
            return render_template('admin/edit_seller.html', seller=seller)
        
        elif request.method == 'POST':
            # Procesar actualización
            try:
                data = request.form.to_dict()
                data['is_active'] = request.form.get('is_active') == 'on'
                
                success, message = SellerService.update(seller_id, data)
                
                if success:
                    flash(message, 'success')
                    AdminLogger.log_action('UPDATE_SELLER_SUCCESS', session.get('user_id'), 'seller', seller_id, data)
                    return redirect(url_for('admin_sellers'))
                else:
                    flash(message, 'error')
                    AdminLogger.log_action('UPDATE_SELLER_FAILED', session.get('user_id'), 'seller', seller_id, message)
                    return redirect(url_for('admin_edit_seller_improved', seller_id=seller_id))
                    
            except Exception as e:
                error_msg = f'Error actualizando vendedor: {str(e)}'
                flash(error_msg, 'error')
                AdminLogger.log_action('UPDATE_SELLER_ERROR', session.get('user_id'), 'seller', seller_id, error_msg)
                return redirect(url_for('admin_edit_seller_improved', seller_id=seller_id))
    
    @app.route('/admin/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
    @admin_required
    @log_admin_action('EDIT_OFFER', 'offer')
    def admin_edit_offer_improved(offer_id):
        """Editar oferta con validación mejorada"""
        if request.method == 'GET':
            # Mostrar formulario de edición
            offer = OfferService.get_by_id(offer_id)
            if not offer:
                flash('Oferta no encontrada', 'error')
                return redirect(url_for('admin_offers'))
            
            AdminLogger.log_action('VIEW_OFFER_EDIT', session.get('user_id'), 'offer', offer_id)
            return render_template('admin/edit_offer.html', offer=offer)
        
        elif request.method == 'POST':
            # Procesar actualización
            try:
                data = request.form.to_dict()
                data['is_active'] = request.form.get('is_active') == 'on'
                
                success, message = OfferService.update(offer_id, data)
                
                if success:
                    flash(message, 'success')
                    AdminLogger.log_action('UPDATE_OFFER_SUCCESS', session.get('user_id'), 'offer', offer_id, data)
                    return redirect(url_for('admin_offers'))
                else:
                    flash(message, 'error')
                    AdminLogger.log_action('UPDATE_OFFER_FAILED', session.get('user_id'), 'offer', offer_id, message)
                    return redirect(url_for('admin_edit_offer_improved', offer_id=offer_id))
                    
            except Exception as e:
                error_msg = f'Error actualizando oferta: {str(e)}'
                flash(error_msg, 'error')
                AdminLogger.log_action('UPDATE_OFFER_ERROR', session.get('user_id'), 'offer', offer_id, error_msg)
                return redirect(url_for('admin_edit_offer_improved', offer_id=offer_id))
    
    @app.route('/admin/sellers/validate-email', methods=['POST'])
    @admin_required
    def validate_seller_email():
        """Validar email de vendedor en tiempo real"""
        from flask import jsonify
        
        email = request.json.get('email')
        seller_id = request.json.get('seller_id')
        
        if not email:
            return jsonify({'valid': False, 'message': 'Email requerido'})
        
        exists = DatabaseService.entity_exists('sellers', 'email', email, exclude_id=seller_id)
        
        return jsonify({
            'valid': not exists,
            'message': 'Email ya existe' if exists else 'Email disponible'
        })
    
    @app.route('/admin/audit-log')
    @admin_required
    def admin_audit_log():
        """Ver log de auditoría administrativa"""
        try:
            with get_db_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_audit_log 
                    ORDER BY created_at DESC 
                    LIMIT 100
                """)
                logs = cursor.fetchall()
            
            return render_template('admin/audit_log.html', logs=logs)
        
        except Exception as e:
            flash(f'Error cargando logs de auditoría: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))
    
    return app

# Función para crear tabla de auditoría si no existe
def create_audit_table():
    """Crear tabla de auditoría administrativa"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_audit_log (
                    id SERIAL PRIMARY KEY,
                    action VARCHAR(100) NOT NULL,
                    user_id INTEGER NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices para mejor performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON admin_audit_log(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON admin_audit_log(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_action ON admin_audit_log(action)
            """)
            
    except Exception as e:
        print(f"Error creando tabla de auditoría: {e}")

if __name__ == "__main__":
    # Crear tabla de auditoría al importar
    create_audit_table()