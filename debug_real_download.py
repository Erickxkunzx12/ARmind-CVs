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

def debug_download_cover_letter_step_by_step():
    """Debug paso a paso de la función download_cover_letter"""
    
    print("=== INICIANDO DEBUG DE DOWNLOAD_COVER_LETTER ===")
    
    # Simular los parámetros que llegan a la función
    cover_letter_id = 9  # Del terminal vemos que se está descargando el ID 9
    user_id = 40  # Asumiendo el user_id del usuario logueado
    
    print(f"Parámetros: cover_letter_id={cover_letter_id}, user_id={user_id}")
    
    # Paso 1: Conexión a la base de datos
    connection = get_db_connection()
    if not connection:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    print("✅ Conexión a la base de datos exitosa")
    
    # Paso 2: Ejecutar la consulta
    cursor = connection.cursor()
    query = """
        SELECT job_title, company_name, content, language, created_at
        FROM cover_letters 
        WHERE id = %s AND user_id = %s
    """
    
    print(f"Ejecutando consulta: {query}")
    print(f"Con parámetros: ({cover_letter_id}, {user_id})")
    
    cursor.execute(query, (cover_letter_id, user_id))
    
    # Paso 3: Obtener los datos
    cover_letter_data = cursor.fetchone()
    cursor.close()
    connection.close()
    
    print(f"Datos obtenidos: {cover_letter_data}")
    
    if not cover_letter_data:
        print("ERROR: No se encontraron datos")
        return
    
    # Paso 4: Unpacking
    print("\n=== UNPACKING DE DATOS ===")
    print(f"cover_letter_data = {cover_letter_data}")
    print(f"Tipo: {type(cover_letter_data)}")
    print(f"Longitud: {len(cover_letter_data)}")
    
    job_title, company_name, content, language, created_at = cover_letter_data
    
    print(f"\n=== VARIABLES DESPUÉS DEL UNPACKING ===")
    print(f"job_title = {repr(job_title)} (tipo: {type(job_title)})")
    print(f"company_name = {repr(company_name)} (tipo: {type(company_name)})")
    print(f"content = {repr(content[:100])}... (tipo: {type(content)})")
    print(f"language = {repr(language)} (tipo: {type(language)})")
    print(f"created_at = {repr(created_at)} (tipo: {type(created_at)})")
    
    # Paso 5: Verificar si las variables son strings literales
    if job_title == 'job_title':
        print("🚨 ERROR: job_title contiene el literal 'job_title'")
    if company_name == 'company_name':
        print("🚨 ERROR: company_name contiene el literal 'company_name'")
    if content == 'content':
        print("🚨 ERROR: content contiene el literal 'content'")
    if language == 'language':
        print("🚨 ERROR: language contiene el literal 'language'")
    
    # Paso 6: Configuración de idioma
    language_config = {
        'es': {'title': 'Carta de Presentación', 'closing': 'Atentamente'},
        'en': {'title': 'Cover Letter', 'closing': 'Sincerely'},
        'pt': {'title': 'Carta de Apresentação', 'closing': 'Atenciosamente'},
        'de': {'title': 'Anschreiben', 'closing': 'Mit freundlichen Grüßen'},
        'fr': {'title': 'Lettre de Motivation', 'closing': 'Cordialement'}
    }
    
    lang_config = language_config.get(language, language_config['es'])
    
    print(f"\n=== CONFIGURACIÓN DE IDIOMA ===")
    print(f"language = {language}")
    print(f"lang_config = {lang_config}")
    
    # Paso 7: Formatear contenido
    paragraphs = content.split('\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            formatted_paragraphs.append(f'<p>{para}</p>')
    
    formatted_content = '\n'.join(formatted_paragraphs)
    
    print(f"\n=== CONTENIDO FORMATEADO ===")
    print(f"Párrafos originales: {len(paragraphs)}")
    print(f"Párrafos formateados: {len(formatted_paragraphs)}")
    print(f"Contenido formateado (primeros 200 chars): {formatted_content[:200]}...")
    
    # Paso 8: Generar HTML
    print(f"\n=== GENERANDO HTML ===")
    print(f"Variables para interpolación:")
    print(f"  lang_config['title'] = {lang_config['title']}")
    print(f"  job_title = {job_title}")
    print(f"  company_name = {company_name}")
    print(f"  formatted_content = {formatted_content[:50]}...")
    print(f"  lang_config['closing'] = {lang_config['closing']}")
    
    # Simular session
    username = "erick_kunz"  # Del terminal
    
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
                {username}</p>
            </div>
        </body>
        </html>
        """
    
    print(f"\n=== HTML GENERADO (primeros 500 chars) ===")
    print(html_content[:500])
    
    # Verificar interpolación
    if '{job_title}' in html_content:
        print("\n🚨 ERROR: job_title no se interpoló")
    if '{company_name}' in html_content:
        print("\n🚨 ERROR: company_name no se interpoló")
    if '{formatted_content}' in html_content:
        print("\n🚨 ERROR: formatted_content no se interpoló")
    
    if ('{job_title}' not in html_content and 
        '{company_name}' not in html_content and 
        '{formatted_content}' not in html_content):
        print("\n✅ Todas las variables se interpolaron correctamente")
    
    print("\n=== FIN DEL DEBUG ===")

if __name__ == "__main__":
    debug_download_cover_letter_step_by_step()