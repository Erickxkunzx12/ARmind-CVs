# Rutas del administrador para el sistema de ventas, cupones y ofertas
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, make_response, session
from functools import wraps
from datetime import datetime, timedelta
import json
from admin_sales_system import (
    init_sales_tables, create_coupon, get_coupons, update_coupon, delete_coupon,
    create_offer, get_offers, get_sales_summary, export_sales_report,
    get_db_connection, update_seller, update_offer, get_seller_by_id, get_offer_by_id
)
from psycopg2.extras import RealDictCursor

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_admin_sales_routes(app):
    """Registrar todas las rutas del sistema de ventas en la aplicación Flask"""
    
    # Inicializar tablas al registrar rutas
    with app.app_context():
        init_sales_tables()
    
    @app.route('/admin/sales')
    @admin_required
    def admin_sales_dashboard():
        """Dashboard principal del sistema de ventas"""
        try:
            # Obtener estadísticas generales
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Estadísticas de cupones
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_coupons,
                    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_coupons,
                    SUM(usage_count) as total_usage
                FROM discount_coupons
            """)
            coupon_stats = cursor.fetchone()
            
            # Estadísticas de ofertas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_offers,
                    COUNT(CASE WHEN status = 'active' AND start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE THEN 1 END) as active_offers,
                    COUNT(CASE WHEN end_date < CURRENT_DATE THEN 1 END) as expired_offers
                FROM promotional_offers
            """)
            offer_stats = cursor.fetchone()
            
            # Estadísticas de ventas del mes actual
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_transactions,
                    COALESCE(SUM(final_amount), 0) as total_revenue,
                    COALESCE(SUM(commission_amount), 0) as total_commissions
                FROM sales_transactions
                WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
                AND status = 'completed'
            """)
            sales_stats = cursor.fetchone()
            
            # Ventas recientes
            cursor.execute("""
                SELECT st.*, s.name as seller_name, u.username
                FROM sales_transactions st
                LEFT JOIN sellers s ON st.seller_id = s.id
                LEFT JOIN users u ON st.user_id = u.id
                ORDER BY st.created_at DESC
                LIMIT 10
            """)
            recent_sales = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return render_template('admin/sales_dashboard.html',
                                 coupon_stats=coupon_stats,
                                 offer_stats=offer_stats,
                                 sales_stats=sales_stats,
                                 recent_sales=recent_sales)
                                 
        except Exception as e:
            flash(f'Error cargando dashboard: {e}', 'error')
            return redirect(url_for('admin_dashboard'))
    
    # === RUTAS DE CUPONES ===
    
    @app.route('/admin/coupons')
    @admin_required
    def admin_coupons():
        """Gestión de cupones de descuento"""
        try:
            # Obtener parámetros de filtro
            seller_id = request.args.get('seller_id', type=int)
            is_active = request.args.get('is_active')
            search_term = request.args.get('search', '')
            page = request.args.get('page', 1, type=int)
            
            # Convertir is_active a boolean si está presente
            if is_active == 'true':
                is_active = True
            elif is_active == 'false':
                is_active = False
            else:
                is_active = None
            
            # Obtener cupones
            coupons = get_coupons(seller_id, is_active, search_term, page)
            
            # Obtener lista de vendedores para el filtro
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, name FROM sellers WHERE is_active = TRUE ORDER BY name")
            sellers = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return render_template('admin/coupons.html',
                                 coupons=coupons,
                                 sellers=sellers,
                                 current_filters={
                                     'seller_id': seller_id,
                                     'is_active': request.args.get('is_active'),
                                     'search': search_term,
                                     'page': page
                                 })
                                 
        except Exception as e:
            flash(f'Error cargando cupones: {e}', 'error')
            return redirect(url_for('admin_sales_dashboard'))
    
    @app.route('/admin/coupons/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_coupon():
        """Crear nuevo cupón"""
        if request.method == 'GET':
            # Obtener lista de vendedores
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, name FROM sellers WHERE is_active = TRUE ORDER BY name")
            sellers = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return render_template('admin/create_coupon.html', sellers=sellers)
        
        try:
            # Obtener datos del formulario
            code = request.form.get('code', '').strip().upper()
            discount_percentage = float(request.form.get('discount_percentage', 0))
            seller_id = int(request.form.get('seller_id'))
            commission_percentage = float(request.form.get('commission_percentage', 0))
            max_usage = request.form.get('max_usage')
            valid_until = request.form.get('valid_until')
            
            # Validaciones
            if not code:
                flash('El código del cupón es requerido', 'error')
                return redirect(url_for('admin_create_coupon'))
            
            if discount_percentage <= 0 or discount_percentage > 100:
                flash('El porcentaje de descuento debe estar entre 1 y 100', 'error')
                return redirect(url_for('admin_create_coupon'))
            
            if commission_percentage < 0 or commission_percentage > 100:
                flash('El porcentaje de comisión debe estar entre 0 y 100', 'error')
                return redirect(url_for('admin_create_coupon'))
            
            # Convertir valores opcionales
            max_usage = int(max_usage) if max_usage else None
            valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date() if valid_until else None
            
            # Crear cupón
            success, message = create_coupon(code, discount_percentage, seller_id, commission_percentage, max_usage, valid_until)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('admin_coupons'))
            else:
                flash(message, 'error')
                return redirect(url_for('admin_create_coupon'))
                
        except Exception as e:
            flash(f'Error creando cupón: {e}', 'error')
            return redirect(url_for('admin_create_coupon'))
    
    @app.route('/admin/coupons/edit/<int:coupon_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_coupon(coupon_id):
        """Editar cupón existente"""
        if request.method == 'GET':
            try:
                # Obtener datos del cupón
                connection = get_db_connection()
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT dc.*, s.name as seller_name
                    FROM discount_coupons dc
                    LEFT JOIN sellers s ON dc.seller_id = s.id
                    WHERE dc.id = %s
                """, (coupon_id,))
                coupon = cursor.fetchone()
                
                if not coupon:
                    flash('Cupón no encontrado', 'error')
                    return redirect(url_for('admin_coupons'))
                
                # Obtener lista de vendedores
                cursor.execute("SELECT id, name FROM sellers WHERE is_active = TRUE ORDER BY name")
                sellers = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                return render_template('admin/edit_coupon.html', coupon=coupon, sellers=sellers)
                
            except Exception as e:
                flash(f'Error cargando cupón: {e}', 'error')
                return redirect(url_for('admin_coupons'))
        
        try:
            # Obtener datos del formulario
            data = {}
            
            if 'discount_percentage' in request.form:
                data['discount_percentage'] = float(request.form.get('discount_percentage'))
            
            if 'commission_percentage' in request.form:
                data['commission_percentage'] = float(request.form.get('commission_percentage'))
            
            if 'is_active' in request.form:
                data['is_active'] = request.form.get('is_active') == 'true'
            
            if 'max_usage' in request.form:
                max_usage = request.form.get('max_usage')
                data['max_usage'] = int(max_usage) if max_usage else None
            
            if 'valid_until' in request.form:
                valid_until = request.form.get('valid_until')
                data['valid_until'] = datetime.strptime(valid_until, '%Y-%m-%d').date() if valid_until else None
            
            # Actualizar cupón
            success, message = update_coupon(coupon_id, **data)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
            
            return redirect(url_for('admin_coupons'))
            
        except Exception as e:
            flash(f'Error actualizando cupón: {e}', 'error')
            return redirect(url_for('admin_coupons'))
    
    @app.route('/admin/coupons/delete/<int:coupon_id>', methods=['POST'])
    @admin_required
    def admin_delete_coupon(coupon_id):
        """Eliminar cupón"""
        try:
            success, message = delete_coupon(coupon_id)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
            
        except Exception as e:
            flash(f'Error eliminando cupón: {e}', 'error')
        
        return redirect(url_for('admin_coupons'))
    
    @app.route('/admin/coupons/export')
    @admin_required
    def admin_export_coupons():
        """Exportar cupones a CSV"""
        try:
            # Obtener todos los cupones
            coupons = get_coupons(page=1, per_page=10000)  # Obtener todos
            
            # Crear CSV
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Encabezados
            writer.writerow(['Código', 'Descuento %', 'Vendedor', 'Comisión %', 'Activo', 'Usos', 'Máx. Usos', 'Válido Hasta', 'Creado'])
            
            # Datos
            for coupon in coupons:
                writer.writerow([
                    coupon['code'],
                    coupon['discount_percentage'],
                    coupon['seller_name'] or 'N/A',
                    coupon['commission_percentage'],
                    'Sí' if coupon['is_active'] else 'No',
                    coupon['total_usage'],
                    coupon['max_usage'] or 'Ilimitado',
                    coupon['valid_until'] or 'Sin límite',
                    coupon['created_at'].strftime('%Y-%m-%d')
                ])
            
            # Crear respuesta
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=cupones_{datetime.now().strftime("%Y%m%d")}.csv'
            
            return response
            
        except Exception as e:
            flash(f'Error exportando cupones: {e}', 'error')
            return redirect(url_for('admin_coupons'))
    
    # === RUTAS DE OFERTAS ===
    
    @app.route('/admin/offers')
    @admin_required
    def admin_offers():
        """Gestión de ofertas promocionales"""
        try:
            # Obtener parámetros de filtro
            status = request.args.get('status')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            page = request.args.get('page', 1, type=int)
            
            # Preparar filtro de rango de fechas
            date_range = None
            if start_date and end_date:
                date_range = (start_date, end_date)
            
            # Obtener ofertas
            offers = get_offers(status, date_range, page)
            
            return render_template('admin/offers.html',
                                 offers=offers,
                                 current_filters={
                                     'status': status,
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'page': page
                                 })
                                 
        except Exception as e:
            flash(f'Error cargando ofertas: {e}', 'error')
            return redirect(url_for('admin_sales_dashboard'))
    
    @app.route('/admin/offers/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_offer():
        """Crear nueva oferta"""
        if request.method == 'GET':
            return render_template('admin/create_offer.html')
        
        try:
            # Obtener datos del formulario
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            discount_percentage = float(request.form.get('discount_percentage', 0))
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            # Validaciones
            if not title:
                flash('El título de la oferta es requerido', 'error')
                return redirect(url_for('admin_create_offer'))
            
            if discount_percentage <= 0 or discount_percentage > 100:
                flash('El porcentaje de descuento debe estar entre 1 y 100', 'error')
                return redirect(url_for('admin_create_offer'))
            
            if start_date >= end_date:
                flash('La fecha de inicio debe ser anterior a la fecha de fin', 'error')
                return redirect(url_for('admin_create_offer'))
            
            # Crear oferta
            success, message = create_offer(title, description, discount_percentage, start_date, end_date)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('admin_offers'))
            else:
                flash(message, 'error')
                return redirect(url_for('admin_create_offer'))
                
        except Exception as e:
            flash(f'Error creando oferta: {e}', 'error')
            return redirect(url_for('admin_create_offer'))
    
    # === RUTAS DE REPORTES DE VENTAS ===
    
    @app.route('/admin/sales/reports')
    @admin_required
    def admin_sales_reports():
        """Reportes de ventas"""
        try:
            # Obtener parámetros de filtro
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            seller_id = request.args.get('seller_id', type=int)
            group_by = request.args.get('group_by', 'day')
            
            # Obtener datos de ventas
            sales_data = get_sales_summary(start_date, end_date, seller_id, group_by)
            
            # Obtener lista de vendedores y contar activos
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, name FROM sellers WHERE is_active = TRUE ORDER BY name")
            sellers = cursor.fetchall()
            
            # Contar vendedores activos
            cursor.execute("SELECT COUNT(*) as count FROM sellers WHERE is_active = TRUE")
            active_sellers = cursor.fetchone()['count']
            cursor.close()
            connection.close()
            
            # Calcular resumen estadístico
            total_sales = len(sales_data)
            total_amount = sum(float(row['total_final']) for row in sales_data)
            avg_sale = total_amount / total_sales if total_sales > 0 else 0
            
            summary = {
                'total_sales': total_sales,
                'total_amount': total_amount,
                'avg_sale': avg_sale,
                'active_sellers': active_sellers
            }
            
            # Preparar datos para gráficos
            chart_data = {
                'labels': [str(row['period']) for row in sales_data],
                'datasets': [{
                    'label': 'Ventas Totales',
                    'data': [float(row['total_final']) for row in sales_data],
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            }
            
            return render_template('admin/sales_reports.html',
                                 sales_data=sales_data,
                                 sellers=sellers,
                                 summary=summary,
                                 chart_data=json.dumps(chart_data),
                                 current_filters={
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'seller_id': seller_id,
                                     'group_by': group_by
                                 })
                                 
        except Exception as e:
            flash(f'Error cargando reportes: {e}', 'error')
            return redirect(url_for('admin_sales_dashboard'))
    
    @app.route('/admin/sales/export')
    @admin_required
    def admin_export_sales():
        """Exportar reporte de ventas"""
        try:
            # Obtener parámetros
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            seller_id = request.args.get('seller_id', type=int)
            format_type = request.args.get('format', 'csv')
            
            # Exportar datos
            if format_type == 'csv':
                data = export_sales_report(start_date, end_date, seller_id, 'csv')
                response = make_response(data)
                response.headers['Content-Type'] = 'text/csv'
                response.headers['Content-Disposition'] = f'attachment; filename=ventas_{datetime.now().strftime("%Y%m%d")}.csv'
                return response
            
            elif format_type == 'pdf':
                data = export_sales_report(start_date, end_date, seller_id, 'pdf')
                response = make_response(data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=ventas_{datetime.now().strftime("%Y%m%d")}.pdf'
                return response
            
            else:
                flash('Formato de exportación no válido', 'error')
                return redirect(url_for('admin_sales_reports'))
                
        except Exception as e:
            flash(f'Error exportando reporte: {e}', 'error')
            return redirect(url_for('admin_sales_reports'))
    
    # === RUTAS DE VENDEDORES ===
    
    @app.route('/admin/sellers')
    @admin_required
    def admin_sellers():
        """Gestión de vendedores"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT s.*,
                       COUNT(dc.id) as total_coupons,
                       COUNT(st.id) as total_sales,
                       COALESCE(SUM(st.commission_amount), 0) as total_commissions
                FROM sellers s
                LEFT JOIN discount_coupons dc ON s.id = dc.seller_id
                LEFT JOIN sales_transactions st ON s.id = st.seller_id
                GROUP BY s.id
                ORDER BY s.name
            """)
            
            sellers = cursor.fetchall()
            cursor.close()
            connection.close()
            
            # Create current_filters object for template
            current_filters = {
                'search': request.args.get('search', ''),
                'status': request.args.get('status', ''),
                'sort_by': request.args.get('sort_by', 'name')
            }
            
            return render_template('admin/sellers.html', 
                                 sellers=sellers,
                                 current_filters=current_filters)
            
        except Exception as e:
            flash(f'Error cargando vendedores: {e}', 'error')
            return redirect(url_for('admin_sales_dashboard'))
    
    @app.route('/admin/sellers/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_seller():
        """Crear nuevo vendedor"""
        if request.method == 'GET':
            return render_template('admin/create_seller.html')
        
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            commission_rate = float(request.form.get('commission_rate', 10.0))
            
            # Validaciones
            if not name or not email:
                flash('Nombre y email son requeridos', 'error')
                return redirect(url_for('admin_create_seller'))
            
            # Crear vendedor
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO sellers (name, email, phone, commission_rate)
                VALUES (%s, %s, %s, %s)
            """, (name, email, phone, commission_rate))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            flash('Vendedor creado correctamente', 'success')
            return redirect(url_for('admin_sellers'))
            
        except Exception as e:
            flash(f'Error creando vendedor: {e}', 'error')
            return redirect(url_for('admin_create_seller'))
    
    # === API ENDPOINTS ===
    
    @app.route('/api/admin/sales/chart-data')
    @admin_required
    def api_sales_chart_data():
        """API para obtener datos de gráficos de ventas"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            seller_id = request.args.get('seller_id', type=int)
            group_by = request.args.get('group_by', 'day')
            
            sales_data = get_sales_summary(start_date, end_date, seller_id, group_by)
            
            # Formatear datos para Chart.js
            chart_data = {
                'labels': [str(row['period']) for row in sales_data],
                'datasets': [{
                    'label': 'Ventas Totales',
                    'data': [float(row['total_final']) for row in sales_data],
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }, {
                    'label': 'Comisiones',
                    'data': [float(row['total_commission']) for row in sales_data],
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1
                }]
            }
            
            return jsonify(chart_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/validate-coupon-code')
    @admin_required
    def api_validate_coupon_code():
        """API para validar si un código de cupón ya existe"""
        try:
            code = request.args.get('code', '').strip().upper()
            
            if not code:
                return jsonify({'valid': True})
            
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT id FROM discount_coupons WHERE code = %s", (code,))
            exists = cursor.fetchone() is not None
            
            cursor.close()
            connection.close()
            
            return jsonify({'valid': not exists, 'exists': exists})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/sellers/edit/<int:seller_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_seller(seller_id):
        """Editar un vendedor existente"""
        if request.method == 'GET':
            # Mostrar formulario de edición
            seller = get_seller_by_id(seller_id)
            if not seller:
                flash('Vendedor no encontrado', 'error')
                return redirect(url_for('admin_sellers'))
            
            return render_template('admin/edit_seller.html', seller=seller)
        
        elif request.method == 'POST':
            # Procesar actualización
            try:
                data = {
                    'name': request.form.get('name'),
                    'email': request.form.get('email'),
                    'phone': request.form.get('phone'),
                    'commission_rate': float(request.form.get('commission_rate', 0)),
                    'is_active': request.form.get('is_active') == 'on'
                }
                
                # Filtrar campos vacíos
                data = {k: v for k, v in data.items() if v is not None and v != ''}
                
                success, message = update_seller(seller_id, **data)
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('admin_sellers'))
                else:
                    flash(message, 'error')
                    return redirect(url_for('admin_edit_seller', seller_id=seller_id))
                    
            except Exception as e:
                flash(f'Error actualizando vendedor: {str(e)}', 'error')
                return redirect(url_for('admin_edit_seller', seller_id=seller_id))

    @app.route('/admin/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_offer(offer_id):
        """Editar una oferta promocional existente"""
        if request.method == 'GET':
            # Mostrar formulario de edición
            offer = get_offer_by_id(offer_id)
            if not offer:
                flash('Oferta no encontrada', 'error')
                return redirect(url_for('admin_offers'))
            
            return render_template('admin/edit_offer.html', offer=offer)
        
        elif request.method == 'POST':
            # Procesar actualización
            try:
                data = {
                    'title': request.form.get('title'),
                    'description': request.form.get('description'),
                    'discount_percentage': float(request.form.get('discount_percentage', 0)),
                    'start_date': request.form.get('start_date'),
                    'end_date': request.form.get('end_date'),
                    'is_active': request.form.get('is_active') == 'on',
                    'status': request.form.get('status', 'active')
                }
                
                # Filtrar campos vacíos
                data = {k: v for k, v in data.items() if v is not None and v != ''}
                
                success, message = update_offer(offer_id, **data)
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('admin_offers'))
                else:
                    flash(message, 'error')
                    return redirect(url_for('admin_edit_offer', offer_id=offer_id))
                    
            except Exception as e:
                flash(f'Error actualizando oferta: {str(e)}', 'error')
                return redirect(url_for('admin_edit_offer', offer_id=offer_id))

    return app