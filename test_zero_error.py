import psycopg2
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def test_zero_error_scenario():
    """Test scenarios that could cause str(e) to return '0'"""
    
    print("=== PROBANDO ESCENARIOS QUE CAUSAN ERROR '0' ===")
    
    # Escenario 1: División por cero
    try:
        result = 1 / 0
    except Exception as e:
        print(f"División por cero - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
    
    # Escenario 2: Error de base de datos con código 0
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Intentar una consulta que podría fallar
        cur.execute("SELECT * FROM non_existent_table")
        
    except Exception as e:
        print(f"Error de DB - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
        if hasattr(e, 'pgcode'):
            print(f"Código PG: {e.pgcode}")
    
    # Escenario 3: Error de conexión
    try:
        bad_config = DB_CONFIG.copy()
        bad_config['port'] = 0  # Puerto inválido
        conn = psycopg2.connect(**bad_config)
        
    except Exception as e:
        print(f"Error de conexión - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
    
    # Escenario 4: Error de JSON
    try:
        json.loads("invalid json")
    except Exception as e:
        print(f"Error de JSON - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
    
    # Escenario 5: KeyError con 0
    try:
        data = {}
        value = data[0]
    except Exception as e:
        print(f"KeyError con 0 - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
    
    # Escenario 6: IndexError
    try:
        lista = []
        value = lista[0]
    except Exception as e:
        print(f"IndexError - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")

def test_session_key_error():
    """Test session key error that might cause the issue"""
    
    print("\n=== PROBANDO ERROR DE SESIÓN ===")
    
    # Simular el error que podría ocurrir en export_cv
    try:
        # Simular session sin user_id
        session = {}
        user_id = session['user_id']  # Esto causará KeyError
        
    except Exception as e:
        print(f"Error de sesión - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
        
        # Verificar si este es el error que causa "0"
        if str(e) == "'user_id'":
            print("✅ Este podría ser el problema - KeyError de user_id")

def test_database_connection_error():
    """Test database connection issues"""
    
    print("\n=== PROBANDO ERRORES DE BASE DE DATOS ===")
    
    # Escenario 1: Conexión cerrada prematuramente
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        conn.close()  # Cerrar conexión
        
        # Intentar usar cursor después de cerrar conexión
        cur.execute("SELECT 1")
        
    except Exception as e:
        print(f"Conexión cerrada - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
    
    # Escenario 2: Cursor cerrado
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.close()  # Cerrar cursor
        
        # Intentar usar cursor cerrado
        cur.execute("SELECT 1")
        
    except Exception as e:
        print(f"Cursor cerrado - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
        conn.close()

def test_specific_export_error():
    """Test the specific error that might occur in export_cv"""
    
    print("\n=== PROBANDO ERROR ESPECÍFICO DE EXPORT ===")
    
    try:
        # Usar configuración directa
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Simular la consulta de export_cv con datos que podrían causar error
        cur.execute(
            "SELECT filename FROM resumes WHERE id = %s AND user_id = %s",
            (999999, 999999)  # IDs que no existen
        )
        result = cur.fetchone()
        
        if not result:
            # Simular el error que podría ocurrir
            raise Exception(0)  # Excepción con valor 0
            
    except Exception as e:
        print(f"Error simulado - str(e): '{str(e)}'")
        print(f"Tipo de excepción: {type(e)}")
        
        if str(e) == "0":
            print("🎯 ENCONTRADO: Este es el error que causa 'Error al obtener CV: 0'")
        
        conn.close()

if __name__ == "__main__":
    test_zero_error_scenario()
    test_session_key_error()
    test_database_connection_error()
    test_specific_export_error()