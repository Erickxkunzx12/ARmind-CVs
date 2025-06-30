import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Cargar variables de entorno
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL con manejo de errores mejorado"""
    try:
        # Usar opciones adicionales para manejar problemas de codificación
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor,
            client_encoding='UTF8',
            options="-c client_encoding=UTF8"
        )
        
        return connection
    except psycopg2.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def debug_download_function():
    """Debug específico para la función download_cover_letter"""
    try:
        # Usar el ID de la carta más reciente
        cover_letter_id = 11  # Basado en los logs del terminal
        user_id = 40  # Basado en los logs anteriores
        
        print(f"=== DEBUG: Función download_cover_letter ===")
        print(f"Cover Letter ID: {cover_letter_id}")
        print(f"User ID: {user_id}")
        print()
        
        connection = get_db_connection()
        if not connection:
            print("❌ Error de conexión a la base de datos")
            return
        
        cursor = connection.cursor()
        cursor.execute("""
            SELECT job_title, company_name, content, language, created_at
            FROM cover_letters 
            WHERE id = %s AND user_id = %s
        """, (cover_letter_id, user_id))
        
        cover_letter_data = cursor.fetchone()
        print(f"Raw data type: {type(cover_letter_data)}")
        print(f"Raw data: {cover_letter_data}")
        print()
        
        if not cover_letter_data:
            print("❌ Carta de presentación no encontrada")
            cursor.close()
            connection.close()
            return
        
        # Verificar si es un diccionario (RealDictCursor) o tupla
        if isinstance(cover_letter_data, dict):
            print("✅ Los datos son un diccionario (RealDictCursor)")
            job_title = cover_letter_data['job_title']
            company_name = cover_letter_data['company_name']
            content = cover_letter_data['content']
            language = cover_letter_data['language']
            created_at = cover_letter_data['created_at']
        else:
            print("✅ Los datos son una tupla")
            job_title, company_name, content, language, created_at = cover_letter_data
        
        print(f"Job Title: '{job_title}'")
        print(f"Company Name: '{company_name}'")
        print(f"Language: '{language}'")
        print(f"Content (primeros 100 chars): '{content[:100]}...'")
        print(f"Created at: {created_at}")
        print()
        
        # Configuración de idiomas para el PDF
        language_config = {
            'es': {'title': 'Carta de Presentación', 'closing': 'Atentamente'},
            'en': {'title': 'Cover Letter', 'closing': 'Sincerely'},
            'pt': {'title': 'Carta de Apresentação', 'closing': 'Atenciosamente'},
            'de': {'title': 'Anschreiben', 'closing': 'Mit freundlichen Grüßen'},
            'fr': {'title': 'Lettre de Motivation', 'closing': 'Cordialement'}
        }
        
        lang_config = language_config.get(language, language_config['es'])
        print(f"Lang config: {lang_config}")
        
        # Procesar el contenido para preservar los saltos de línea
        paragraphs = content.split('\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:  # Solo agregar párrafos no vacíos
                formatted_paragraphs.append(f'<p>{para}</p>')
        
        formatted_content = '\n'.join(formatted_paragraphs)
        
        print(f"Formatted content (primeros 200 chars): {formatted_content[:200]}...")
        print()
        
        # Simular la construcción del HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .content {{ text-align: justify; margin-bottom: 30px; }}
                .content p {{ margin-bottom: 15px; }}
                .signature {{ margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{lang_config['title']}</h1>
                <p><strong>{job_title}</strong> - {company_name}</p>
            </div>
            <div class="content">
                {formatted_content}
            </div>
            <div class="signature">
                <p>{lang_config['closing']},<br>
                erick_kunz</p>
            </div>
        </body>
        </html>
        """
        
        print("=== HTML GENERADO ===")
        print(html_content[:500] + "...")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error en debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_download_function()