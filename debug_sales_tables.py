import psycopg2
from psycopg2.extras import RealDictCursor
import os
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

def check_sales_tables():
    """Verificar si las tablas del sistema de ventas existen"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Verificar tablas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('sellers', 'discount_coupons', 'promotional_offers', 'sales_transactions')
            ORDER BY table_name
        """)
        
        existing_tables = cursor.fetchall()
        print("\n=== TABLAS DEL SISTEMA DE VENTAS ===")
        print(f"Tablas encontradas: {len(existing_tables)}")
        for table in existing_tables:
            print(f"✅ {table['table_name']}")
        
        # Verificar estructura de la tabla sellers
        print("\n=== ESTRUCTURA DE LA TABLA SELLERS ===")
        try:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'sellers' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            if columns:
                for col in columns:
                    print(f"- {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            else:
                print("❌ Tabla 'sellers' no encontrada")
        except Exception as e:
            print(f"❌ Error verificando estructura de sellers: {e}")
        
        # Verificar datos en sellers
        print("\n=== DATOS EN TABLA SELLERS ===")
        try:
            cursor.execute("SELECT COUNT(*) as total FROM sellers")
            count = cursor.fetchone()
            print(f"Total de vendedores: {count['total']}")
            
            if count['total'] > 0:
                cursor.execute("SELECT * FROM sellers LIMIT 3")
                sellers = cursor.fetchall()
                for seller in sellers:
                    print(f"- ID: {seller.get('id')}, Nombre: {seller.get('name')}, Email: {seller.get('email')}")
        except Exception as e:
            print(f"❌ Error consultando datos de sellers: {e}")
        
        # Verificar función get_sales_summary
        print("\n=== VERIFICANDO FUNCIÓN GET_SALES_SUMMARY ===")
        try:
            from admin_sales_system import get_sales_summary
            sales_data = get_sales_summary(None, None, None, 'day')
            print(f"✅ Función get_sales_summary ejecutada correctamente")
            print(f"Registros devueltos: {len(sales_data)}")
        except Exception as e:
            print(f"❌ Error en get_sales_summary: {e}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")

if __name__ == "__main__":
    check_sales_tables()