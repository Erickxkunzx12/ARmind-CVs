# Sistema de gestión de cupones, ofertas y ventas para el panel de administrador
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import csv
import io
from flask import jsonify, request, render_template, redirect, url_for, flash, make_response, session
from functools import wraps
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'armind_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def init_sales_tables():
    """Inicializar las tablas del sistema de ventas"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Tabla de vendedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(50),
                commission_rate DECIMAL(5,2) DEFAULT 10.00,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de cupones de descuento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discount_coupons (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                discount_percentage DECIMAL(5,2) NOT NULL,
                seller_id INTEGER REFERENCES sellers(id) ON DELETE CASCADE,
                commission_percentage DECIMAL(5,2) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                max_usage INTEGER DEFAULT NULL,
                valid_from DATE DEFAULT CURRENT_DATE,
                valid_until DATE DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de ofertas promocionales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotional_offers (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                discount_percentage DECIMAL(5,2) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_dates CHECK (end_date >= start_date)
            )
        """)
        
        # Tabla de transacciones de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                seller_id INTEGER REFERENCES sellers(id) ON DELETE SET NULL,
                coupon_id INTEGER REFERENCES discount_coupons(id) ON DELETE SET NULL,
                offer_id INTEGER REFERENCES promotional_offers(id) ON DELETE SET NULL,
                subscription_plan VARCHAR(50) NOT NULL,
                original_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0.00,
                final_amount DECIMAL(10,2) NOT NULL,
                commission_amount DECIMAL(10,2) DEFAULT 0.00,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                status VARCHAR(20) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de uso de cupones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id SERIAL PRIMARY KEY,
                coupon_id INTEGER REFERENCES discount_coupons(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                transaction_id INTEGER REFERENCES sales_transactions(id) ON DELETE CASCADE,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(coupon_id, user_id)
            )
        """)
        
        # Índices para optimizar consultas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_transactions_date ON sales_transactions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_transactions_seller ON sales_transactions(seller_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coupon_usage_coupon ON coupon_usage(coupon_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_promotional_offers_dates ON promotional_offers(start_date, end_date)")
        
        # Insertar vendedor por defecto (casa matriz)
        cursor.execute("""
            INSERT INTO sellers (name, email, commission_rate, is_active)
            VALUES ('Casa Matriz', 'admin@armind.com', 0.00, TRUE)
            ON CONFLICT (email) DO NOTHING
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Tablas del sistema de ventas creadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas del sistema de ventas: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False

# Funciones para gestión de cupones
def create_coupon(code, discount_percentage, seller_id, commission_percentage, max_usage=None, valid_until=None):
    """Crear un nuevo cupón de descuento"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Verificar que el código no exista
        cursor.execute("SELECT id FROM discount_coupons WHERE code = %s", (code,))
        if cursor.fetchone():
            return False, "El código del cupón ya existe"
        
        # Crear el cupón
        cursor.execute("""
            INSERT INTO discount_coupons (code, discount_percentage, seller_id, commission_percentage, max_usage, valid_until)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (code, discount_percentage, seller_id, commission_percentage, max_usage, valid_until))
        
        coupon_id = cursor.fetchone()['id']
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, f"Cupón creado con ID: {coupon_id}"
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error creando cupón: {e}"

def get_coupons(seller_id=None, is_active=None, search_term=None, page=1, per_page=20):
    """Obtener lista de cupones con filtros"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Construir consulta con filtros
        where_conditions = []
        params = []
        
        if seller_id:
            where_conditions.append("dc.seller_id = %s")
            params.append(seller_id)
        
        if is_active is not None:
            where_conditions.append("dc.is_active = %s")
            params.append(is_active)
        
        if search_term:
            where_conditions.append("(dc.code ILIKE %s OR s.name ILIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Calcular offset para paginación
        offset = (page - 1) * per_page
        
        query = f"""
            SELECT dc.*, s.name as seller_name,
                   COUNT(cu.id) as total_usage
            FROM discount_coupons dc
            LEFT JOIN sellers s ON dc.seller_id = s.id
            LEFT JOIN coupon_usage cu ON dc.id = cu.coupon_id
            {where_clause}
            GROUP BY dc.id, s.name
            ORDER BY dc.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([per_page, offset])
        cursor.execute(query, params)
        coupons = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return coupons
        
    except Exception as e:
        print(f"Error obteniendo cupones: {e}")
        if connection:
            connection.close()
        return []

def update_coupon(coupon_id, **kwargs):
    """Actualizar un cupón existente"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor()
        
        # Construir consulta de actualización dinámicamente
        set_clauses = []
        params = []
        
        allowed_fields = ['discount_percentage', 'commission_percentage', 'is_active', 'max_usage', 'valid_until']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                params.append(value)
        
        if not set_clauses:
            return False, "No hay campos válidos para actualizar"
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(coupon_id)
        
        query = f"""
            UPDATE discount_coupons 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return False, "Cupón no encontrado"
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, "Cupón actualizado correctamente"
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error actualizando cupón: {e}"

def delete_coupon(coupon_id):
    """Eliminar un cupón"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor()
        
        # Verificar si el cupón ha sido usado
        cursor.execute("SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s", (coupon_id,))
        usage_count = cursor.fetchone()[0]
        
        if usage_count > 0:
            # Si ha sido usado, solo desactivar
            cursor.execute("UPDATE discount_coupons SET is_active = FALSE WHERE id = %s", (coupon_id,))
            message = "Cupón desactivado (no se puede eliminar porque ha sido usado)"
        else:
            # Si no ha sido usado, eliminar completamente
            cursor.execute("DELETE FROM discount_coupons WHERE id = %s", (coupon_id,))
            message = "Cupón eliminado correctamente"
        
        if cursor.rowcount == 0:
            return False, "Cupón no encontrado"
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, message
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error eliminando cupón: {e}"

# Funciones para gestión de ofertas
def create_offer(title, description, discount_percentage, start_date, end_date):
    """Crear una nueva oferta promocional"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Verificar que no haya solapamiento de fechas con ofertas activas
        cursor.execute("""
            SELECT id FROM promotional_offers 
            WHERE is_active = TRUE 
            AND status = 'active'
            AND (
                (start_date <= %s AND end_date >= %s) OR
                (start_date <= %s AND end_date >= %s) OR
                (start_date >= %s AND end_date <= %s)
            )
        """, (start_date, start_date, end_date, end_date, start_date, end_date))
        
        if cursor.fetchone():
            return False, "Ya existe una oferta activa en el rango de fechas seleccionado"
        
        # Crear la oferta
        cursor.execute("""
            INSERT INTO promotional_offers (title, description, discount_percentage, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (title, description, discount_percentage, start_date, end_date))
        
        offer_id = cursor.fetchone()['id']
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, f"Oferta creada con ID: {offer_id}"
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error creando oferta: {e}"

def get_offers(status=None, date_range=None, page=1, per_page=20):
    """Obtener lista de ofertas con filtros"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Construir consulta con filtros
        where_conditions = []
        params = []
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        if date_range:
            start_date, end_date = date_range
            where_conditions.append("start_date >= %s AND end_date <= %s")
            params.extend([start_date, end_date])
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Calcular offset para paginación
        offset = (page - 1) * per_page
        
        query = f"""
            SELECT *,
                   CASE 
                       WHEN end_date < CURRENT_DATE THEN 'expired'
                       WHEN start_date > CURRENT_DATE THEN 'scheduled'
                       ELSE 'active'
                   END as current_status
            FROM promotional_offers
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([per_page, offset])
        cursor.execute(query, params)
        offers = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return offers
        
    except Exception as e:
        print(f"Error obteniendo ofertas: {e}")
        if connection:
            connection.close()
        return []

# Funciones para reportes de ventas
def get_sales_summary(start_date=None, end_date=None, seller_id=None, group_by='day'):
    """Obtener resumen de ventas agrupado por periodo"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Determinar el formato de agrupación
        date_format = {
            'day': "DATE(st.created_at)",
            'week': "DATE_TRUNC('week', st.created_at)",
            'month': "DATE_TRUNC('month', st.created_at)",
            'year': "DATE_TRUNC('year', st.created_at)"
        }.get(group_by, "DATE(st.created_at)")
        
        # Construir consulta con filtros
        where_conditions = ["st.status = 'completed'"]
        params = []
        
        if start_date:
            where_conditions.append("DATE(st.created_at) >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("DATE(st.created_at) <= %s")
            params.append(end_date)
        
        if seller_id:
            where_conditions.append("st.seller_id = %s")
            params.append(seller_id)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                {date_format} as period,
                s.name as seller_name,
                COUNT(st.id) as transaction_count,
                SUM(st.original_amount) as total_original,
                SUM(st.discount_amount) as total_discount,
                SUM(st.final_amount) as total_final,
                SUM(st.commission_amount) as total_commission
            FROM sales_transactions st
            LEFT JOIN sellers s ON st.seller_id = s.id
            {where_clause}
            GROUP BY {date_format}, s.name, st.seller_id
            ORDER BY period DESC, s.name
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
        
    except Exception as e:
        print(f"Error obteniendo resumen de ventas: {e}")
        if connection:
            connection.close()
        return []

def export_sales_report(start_date=None, end_date=None, seller_id=None, format='csv'):
    """Exportar reporte de ventas en CSV o PDF"""
    sales_data = get_sales_summary(start_date, end_date, seller_id, 'day')
    
    if format == 'csv':
        return export_to_csv(sales_data)
    elif format == 'pdf':
        return export_to_pdf(sales_data, start_date, end_date)
    else:
        return None

def export_to_csv(data):
    """Exportar datos a CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow(['Fecha', 'Vendedor', 'Transacciones', 'Monto Original', 'Descuento', 'Monto Final', 'Comisión'])
    
    # Escribir datos
    for row in data:
        writer.writerow([
            row['period'],
            row['seller_name'] or 'Casa Matriz',
            row['transaction_count'],
            f"${row['total_original']:.2f}",
            f"${row['total_discount']:.2f}",
            f"${row['total_final']:.2f}",
            f"${row['total_commission']:.2f}"
        ])
    
    output.seek(0)
    return output.getvalue()

def export_to_pdf(data, start_date=None, end_date=None):
    """Exportar datos a PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Contenido
    story = []
    
    # Título
    title = "Reporte de Ventas - ARMind"
    if start_date and end_date:
        title += f"<br/>Período: {start_date} - {end_date}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # Tabla de datos
    table_data = [['Fecha', 'Vendedor', 'Transacciones', 'Monto Original', 'Descuento', 'Monto Final', 'Comisión']]
    
    for row in data:
        table_data.append([
            str(row['period']),
            row['seller_name'] or 'Casa Matriz',
            str(row['transaction_count']),
            f"${row['total_original']:.2f}",
            f"${row['total_discount']:.2f}",
            f"${row['total_final']:.2f}",
            f"${row['total_commission']:.2f}"
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def update_seller(seller_id, **kwargs):
    """Actualizar un vendedor existente"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor()
        
        # Construir consulta de actualización dinámicamente
        set_clauses = []
        params = []
        
        allowed_fields = ['name', 'email', 'phone', 'commission_rate', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                params.append(value)
        
        if not set_clauses:
            return False, "No hay campos válidos para actualizar"
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(seller_id)
        
        query = f"""
            UPDATE sellers 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return False, "Vendedor no encontrado"
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, "Vendedor actualizado correctamente"
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error actualizando vendedor: {e}"

def update_offer(offer_id, **kwargs):
    """Actualizar una oferta promocional existente"""
    connection = get_db_connection()
    if not connection:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = connection.cursor()
        
        # Construir consulta de actualización dinámicamente
        set_clauses = []
        params = []
        
        allowed_fields = ['title', 'description', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'status']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                params.append(value)
        
        if not set_clauses:
            return False, "No hay campos válidos para actualizar"
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(offer_id)
        
        query = f"""
            UPDATE promotional_offers 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return False, "Oferta no encontrada"
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True, "Oferta actualizada correctamente"
        
    except Exception as e:
        if connection:
            connection.rollback()
            connection.close()
        return False, f"Error actualizando oferta: {e}"

def get_seller_by_id(seller_id):
    """Obtener un vendedor por ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM sellers WHERE id = %s", (seller_id,))
        seller = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return seller
        
    except Exception as e:
        print(f"Error obteniendo vendedor: {e}")
        if connection:
            connection.close()
        return None

def get_offer_by_id(offer_id):
    """Obtener una oferta por ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM promotional_offers WHERE id = %s", (offer_id,))
        offer = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return offer
        
    except Exception as e:
        print(f"Error obteniendo oferta: {e}")
        if connection:
            connection.close()
        return None

if __name__ == "__main__":
    # Inicializar tablas al importar el módulo
    init_sales_tables()