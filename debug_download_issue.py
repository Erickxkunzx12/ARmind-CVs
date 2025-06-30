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

def debug_download_query():
    """Debug de la consulta de descarga"""
    try:
        connection = get_db_connection()
        if not connection:
            print("No se pudo conectar a la base de datos")
            return
        
        cursor = connection.cursor()
        
        # Primero, ver todas las cartas disponibles
        print("=== TODAS LAS CARTAS DISPONIBLES ===")
        cursor.execute("""
            SELECT id, user_id, job_title, company_name, LENGTH(content) as content_length, language, created_at
            FROM cover_letters 
            ORDER BY created_at DESC
        """)
        
        all_letters = cursor.fetchall()
        for letter in all_letters:
            print(f"ID: {letter[0]}, User: {letter[1]}, Job: {letter[2]}, Company: {letter[3]}, Content Length: {letter[4]}, Lang: {letter[5]}, Date: {letter[6]}")
        
        if all_letters:
            # Usar la carta más reciente
            latest_letter = all_letters[0]
            cover_letter_id = latest_letter[0]
            user_id = latest_letter[1]
            
            print(f"\n=== PROBANDO CON ID={cover_letter_id}, USER_ID={user_id} ===")
            
            cursor.execute("""
                SELECT job_title, company_name, content, language, created_at
                FROM cover_letters 
                WHERE id = %s AND user_id = %s
            """, (cover_letter_id, user_id))
            
            cover_letter_data = cursor.fetchone()
            
            if cover_letter_data:
                print("=== DATOS OBTENIDOS ===")
                print(f"Datos raw: {cover_letter_data}")
                print(f"Tipo de datos: {type(cover_letter_data)}")
                print(f"Longitud: {len(cover_letter_data)}")
                
                # Desempaquetar como en el código original
                job_title, company_name, content, language, created_at = cover_letter_data
                
                print("\n=== VARIABLES DESEMPAQUETADAS ===")
                print(f"job_title: '{job_title}' (tipo: {type(job_title)})")
                print(f"company_name: '{company_name}' (tipo: {type(company_name)})")
                print(f"content: '{content[:100]}...' (tipo: {type(content)}, longitud: {len(content)})")
                print(f"language: '{language}' (tipo: {type(language)})")
                print(f"created_at: '{created_at}' (tipo: {type(created_at)})")
                
            else:
                print("No se encontraron datos")
        else:
            print("No hay cartas en la base de datos")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_download_query()