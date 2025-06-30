import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'armind_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        connection.autocommit = True
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def debug_latest_cover_letter():
    """Debug de la carta de presentación más reciente"""
    try:
        connection = get_db_connection()
        if not connection:
            print("No se pudo conectar a la base de datos")
            return
        
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Obtener la carta más reciente
        cursor.execute("""
            SELECT id, user_id, job_title, company_name, content, language, created_at
            FROM cover_letters 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        latest_letter = cursor.fetchone()
        
        if latest_letter:
            print("=== CARTA MÁS RECIENTE ===")
            print(f"ID: {latest_letter['id']}")
            print(f"Usuario: {latest_letter['user_id']}")
            print(f"Puesto: {latest_letter['job_title']}")
            print(f"Empresa: {latest_letter['company_name']}")
            print(f"Idioma: {latest_letter['language']}")
            print(f"Fecha: {latest_letter['created_at']}")
            print(f"Longitud del contenido: {len(latest_letter['content'])}")
            print(f"Contenido completo:")
            print("=" * 50)
            print(latest_letter['content'])
            print("=" * 50)
        else:
            print("No se encontraron cartas de presentación")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_latest_cover_letter()