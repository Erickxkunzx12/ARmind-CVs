import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from admin_sales_system import get_sales_summary
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'armind_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        port=os.getenv('DB_PORT', '5432')
    )

def test_admin_sales_reports():
    """Simular la función admin_sales_reports"""
    print("\n=== TESTING ADMIN_SALES_REPORTS ===")
    try:
        # Simular los parámetros de la función
        start_date = None
        end_date = None
        seller_id = None
        period = 'day'
        
        # Obtener datos de ventas
        sales_data = get_sales_summary(start_date, end_date, seller_id, period)
        print(f"✅ get_sales_summary ejecutado correctamente")
        print(f"Datos obtenidos: {len(sales_data)} registros")
        
        # Obtener vendedores
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, name, email, commission_rate, is_active 
            FROM sellers 
            WHERE is_active = true 
            ORDER BY name
        """)
        sellers = cursor.fetchall()
        print(f"✅ Consulta de vendedores exitosa: {len(sellers)} vendedores")
        
        # Calcular estadísticas
        total_sales = sum(float(sale.get('total_amount', 0)) for sale in sales_data)
        total_transactions = len(sales_data)
        avg_sale = total_sales / total_transactions if total_transactions > 0 else 0
        
        print(f"✅ Estadísticas calculadas:")
        print(f"  - Total ventas: ${total_sales:.2f}")
        print(f"  - Total transacciones: {total_transactions}")
        print(f"  - Venta promedio: ${avg_sale:.2f}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en admin_sales_reports: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_sellers():
    """Simular la función admin_sellers"""
    print("\n=== TESTING ADMIN_SELLERS ===")
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Obtener parámetros de filtro (simulados)
        search = None
        status = None
        
        # Construir consulta
        query = "SELECT * FROM sellers WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name ILIKE %s OR email ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if status:
            query += " AND is_active = %s"
            params.append(status == 'active')
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        sellers = cursor.fetchall()
        print(f"✅ Consulta de vendedores exitosa: {len(sellers)} vendedores")
        
        for seller in sellers:
            print(f"  - {seller['name']} ({seller['email']}) - Activo: {seller['is_active']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en admin_sellers: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_rendering():
    """Verificar si los templates se pueden renderizar"""
    print("\n=== TESTING TEMPLATE RENDERING ===")
    try:
        from flask import Flask, render_template
        
        app = Flask(__name__, template_folder='templates')
        
        with app.app_context():
            # Probar renderizado de sales_reports.html
            try:
                template_content = render_template('admin/sales_reports.html', 
                    sales_data=[], 
                    sellers=[], 
                    total_sales=0, 
                    total_transactions=0, 
                    avg_sale=0,
                    start_date=None,
                    end_date=None,
                    seller_id=None,
                    period='day'
                )
                print("✅ Template sales_reports.html renderizado correctamente")
            except Exception as e:
                print(f"❌ Error renderizando sales_reports.html: {e}")
            
            # Probar renderizado de sellers.html
            try:
                template_content = render_template('admin/sellers.html', 
                    sellers=[], 
                    search=None, 
                    status=None
                )
                print("✅ Template sellers.html renderizado correctamente")
            except Exception as e:
                print(f"❌ Error renderizando sellers.html: {e}")
                
    except Exception as e:
        print(f"❌ Error general en template rendering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== DIAGNÓSTICO DE ERRORES EN RUTAS DE VENTAS ===")
    
    # Test 1: Función admin_sales_reports
    reports_ok = test_admin_sales_reports()
    
    # Test 2: Función admin_sellers
    sellers_ok = test_admin_sellers()
    
    # Test 3: Renderizado de templates
    test_template_rendering()
    
    print("\n=== RESUMEN ===")
    print(f"admin_sales_reports: {'✅ OK' if reports_ok else '❌ ERROR'}")
    print(f"admin_sellers: {'✅ OK' if sellers_ok else '❌ ERROR'}")