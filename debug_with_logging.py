import logging
import sys
import os

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_sales_routes.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from admin_sales_system import get_sales_summary, get_db_connection
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template
import traceback

def test_sales_reports_function():
    """Probar la función admin_sales_reports paso a paso"""
    logger.info("=== TESTING ADMIN_SALES_REPORTS FUNCTION ===")
    
    try:
        # Paso 1: Obtener parámetros de filtro
        logger.info("Paso 1: Configurando parámetros")
        start_date = None
        end_date = None
        seller_id = None
        group_by = 'day'
        logger.info(f"Parámetros: start_date={start_date}, end_date={end_date}, seller_id={seller_id}, group_by={group_by}")
        
        # Paso 2: Obtener datos de ventas
        logger.info("Paso 2: Obteniendo datos de ventas")
        sales_data = get_sales_summary(start_date, end_date, seller_id, group_by)
        logger.info(f"Datos de ventas obtenidos: {len(sales_data)} registros")
        
        # Paso 3: Obtener lista de vendedores
        logger.info("Paso 3: Obteniendo lista de vendedores")
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, name, email, commission_rate, is_active 
            FROM sellers 
            WHERE is_active = true 
            ORDER BY name
        """)
        sellers = cursor.fetchall()
        logger.info(f"Vendedores obtenidos: {len(sellers)}")
        
        # Paso 4: Calcular estadísticas
        logger.info("Paso 4: Calculando estadísticas")
        total_sales = sum(float(sale.get('total_amount', 0)) for sale in sales_data)
        total_transactions = len(sales_data)
        avg_sale = total_sales / total_transactions if total_transactions > 0 else 0
        
        logger.info(f"Estadísticas: total_sales={total_sales}, total_transactions={total_transactions}, avg_sale={avg_sale}")
        
        # Paso 5: Preparar datos para gráfico
        logger.info("Paso 5: Preparando datos para gráfico")
        chart_data = []
        for sale in sales_data:
            chart_data.append({
                'date': str(sale.get('sale_date', '')),
                'amount': float(sale.get('total_amount', 0))
            })
        logger.info(f"Datos de gráfico preparados: {len(chart_data)} puntos")
        
        # Paso 6: Probar renderizado de template
        logger.info("Paso 6: Probando renderizado de template")
        app = Flask(__name__, template_folder='templates')
        app.config['SERVER_NAME'] = 'localhost:5000'
        
        with app.app_context():
            try:
                template_content = render_template('admin/sales_reports.html',
                    sales_data=sales_data,
                    sellers=sellers,
                    total_sales=total_sales,
                    total_transactions=total_transactions,
                    avg_sale=avg_sale,
                    start_date=start_date,
                    end_date=end_date,
                    seller_id=seller_id,
                    period=group_by,
                    chart_data=chart_data,
                    current_filters={
                        'start_date': start_date,
                        'end_date': end_date,
                        'seller_id': seller_id,
                        'group_by': group_by
                    }
                )
                logger.info("✅ Template renderizado correctamente")
                logger.info(f"Tamaño del template: {len(template_content)} caracteres")
            except Exception as template_error:
                logger.error(f"❌ Error renderizando template: {template_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        cursor.close()
        connection.close()
        
        logger.info("✅ Función admin_sales_reports completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en admin_sales_reports: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return False

def test_sellers_function():
    """Probar la función admin_sellers paso a paso"""
    logger.info("\n=== TESTING ADMIN_SELLERS FUNCTION ===")
    
    try:
        # Paso 1: Conectar a la base de datos
        logger.info("Paso 1: Conectando a la base de datos")
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Paso 2: Ejecutar consulta de vendedores
        logger.info("Paso 2: Ejecutando consulta de vendedores")
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
        logger.info(f"Vendedores obtenidos: {len(sellers)}")
        
        for seller in sellers:
            logger.info(f"Vendedor: {seller['name']} - Cupones: {seller['total_coupons']} - Ventas: {seller['total_sales']}")
        
        # Paso 3: Probar renderizado de template
        logger.info("Paso 3: Probando renderizado de template")
        app = Flask(__name__, template_folder='templates')
        app.config['SERVER_NAME'] = 'localhost:5000'
        
        with app.app_context():
            try:
                template_content = render_template('admin/sellers.html',
                    sellers=sellers,
                    search=None,
                    status=None
                )
                logger.info("✅ Template renderizado correctamente")
                logger.info(f"Tamaño del template: {len(template_content)} caracteres")
            except Exception as template_error:
                logger.error(f"❌ Error renderizando template: {template_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        cursor.close()
        connection.close()
        
        logger.info("✅ Función admin_sellers completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en admin_sellers: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("=== DIAGNÓSTICO DETALLADO DE ERRORES EN RUTAS DE VENTAS ===")
    
    # Test 1: Función admin_sales_reports
    reports_ok = test_sales_reports_function()
    
    # Test 2: Función admin_sellers
    sellers_ok = test_sellers_function()
    
    logger.info("\n=== RESUMEN FINAL ===")
    logger.info(f"admin_sales_reports: {'✅ OK' if reports_ok else '❌ ERROR'}")
    logger.info(f"admin_sellers: {'✅ OK' if sellers_ok else '❌ ERROR'}")
    
    if not reports_ok or not sellers_ok:
        logger.error("\n❌ Se encontraron errores. Revisa el archivo debug_sales_routes.log para más detalles.")
    else:
        logger.info("\n✅ Todas las funciones pasaron las pruebas. El problema podría estar en otro lugar.")