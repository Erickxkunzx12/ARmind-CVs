import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def debug_database_content():
    """Debug para verificar el contenido real de la base de datos"""
    try:
        # Conectar a la base de datos
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Obtener todas las cartas de presentación
        cursor.execute("""
            SELECT id, user_id, job_title, company_name, content, language, created_at
            FROM cover_letters 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        print("=== DEBUG: Contenido de la base de datos ===")
        print(f"Total de registros encontrados: {len(results)}")
        print()
        
        for i, row in enumerate(results, 1):
            id_val, user_id, job_title, company_name, content, language, created_at = row
            print(f"--- Registro {i} ---")
            print(f"ID: {id_val}")
            print(f"User ID: {user_id}")
            print(f"Job Title: '{job_title}'")
            print(f"Company Name: '{company_name}'")
            print(f"Language: '{language}'")
            print(f"Content (primeros 200 chars): '{content[:200]}...'")
            print(f"Content type: {type(content)}")
            print(f"Content length: {len(content) if content else 0}")
            print(f"Created at: {created_at}")
            print()
            
            # Verificar si el contenido son literales
            if content and content.strip() == 'content':
                print("⚠️  PROBLEMA: El contenido es literal 'content'")
            if job_title and job_title.strip() == 'job_title':
                print("⚠️  PROBLEMA: El job_title es literal 'job_title'")
            if company_name and company_name.strip() == 'company_name':
                print("⚠️  PROBLEMA: El company_name es literal 'company_name'")
            print()
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")

if __name__ == "__main__":
    debug_database_content()