import psycopg2
from psycopg2.extras import RealDictCursor
import os
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

def check_users():
    """Verificar usuarios en la base de datos"""
    try:
        # Conectar usando configuración directa
        conn = psycopg2.connect(
            **DB_CONFIG,
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users LIMIT 10')
        users = cursor.fetchall()
        
        print('Usuarios en la base de datos:')
        if users:
            for user in users:
                print(f'ID: {user["id"]}, Username: {user["username"]}, Email: {user["email"]}')
        else:
            print('No hay usuarios en la base de datos')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_users()