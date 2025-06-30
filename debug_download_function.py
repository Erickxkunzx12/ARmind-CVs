#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
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
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def simulate_download_cover_letter():
    """Simular exactamente la función download_cover_letter"""
    
    # Obtener la carta más reciente
    connection = get_db_connection()
    if not connection:
        print("Error de conexión a la base de datos")
        return
    
    cursor = connection.cursor()
    
    # Primero obtener la carta más reciente
    cursor.execute("""
        SELECT id, user_id FROM cover_letters 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    latest = cursor.fetchone()
    if not latest:
        print("No hay cartas en la base de datos")
        return
    
    cover_letter_id, user_id = latest
    print(f"Usando cover_letter_id: {cover_letter_id}, user_id: {user_id}")
    
    # Ahora simular la consulta exacta de download_cover_letter
    cursor.execute("""
        SELECT job_title, company_name, content, language, created_at
        FROM cover_letters 
        WHERE id = %s AND user_id = %s
    """, (cover_letter_id, user_id))
    
    cover_letter_data = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not cover_letter_data:
        print('Carta de presentación no encontrada')
        return
    
    # Unpacking exacto como en la función original
    job_title, company_name, content, language, created_at = cover_letter_data
    
    print(f"\n=== DATOS OBTENIDOS ===")
    print(f"job_title: {repr(job_title)}")
    print(f"company_name: {repr(company_name)}")
    print(f"content: {repr(content[:100])}...")
    print(f"language: {repr(language)}")
    print(f"created_at: {repr(created_at)}")
    
    # Configuración de idioma exacta como en la función original
    lang_configs = {
        'es': {'title': 'Carta de Presentación', 'closing': 'Atentamente'},
        'en': {'title': 'Cover Letter', 'closing': 'Sincerely'},
        'pt': {'title': 'Carta de Apresentação', 'closing': 'Atenciosamente'},
        'de': {'title': 'Anschreiben', 'closing': 'Mit freundlichen Grüßen'},
        'fr': {'title': 'Lettre de Motivation', 'closing': 'Cordialement'}
    }
    
    lang_config = lang_configs.get(language, lang_configs['es'])
    
    print(f"\n=== CONFIGURACIÓN DE IDIOMA ===")
    print(f"language: {language}")
    print(f"lang_config: {lang_config}")
    
    # Formatear contenido exacto como en la función original
    paragraphs = content.split('\n\n')
    formatted_content = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    
    print(f"\n=== CONTENIDO FORMATEADO ===")
    print(f"Original content: {content[:200]}...")
    print(f"Formatted content: {formatted_content[:200]}...")
    
    # Simular session
    class MockSession:
        def get(self, key, default):
            return "Usuario Test"
    
    session = MockSession()
    
    # Generar HTML exacto como en la función original
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
                {session.get('username', 'Candidato')}</p>
            </div>
        </body>
        </html>
        """
    
    print(f"\n=== HTML GENERADO ===")
    print(html_content[:500])
    print("...")
    
    # Verificar si las variables se están interpolando
    if '{job_title}' in html_content or '{company_name}' in html_content:
        print("\nERROR: Las variables no se están interpolando!")
    else:
        print("\nOK: Las variables se están interpolando correctamente")

if __name__ == "__main__":
    simulate_download_cover_letter()