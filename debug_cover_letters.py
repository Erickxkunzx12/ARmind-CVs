#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
        return connection
    except psycopg2.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def debug_cover_letters():
    """Debuggear cartas de presentación en la base de datos"""
    connection = get_db_connection()
    if not connection:
        print("No se pudo conectar a la base de datos")
        return
    
    cursor = connection.cursor()
    
    # Verificar si existe la tabla
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'cover_letters'
        )
    """)
    
    result = cursor.fetchone()
    table_exists = result['exists'] if result else False
    print(f"Tabla cover_letters existe: {table_exists}")
    
    if table_exists:
        # Obtener todas las cartas
        cursor.execute("""
            SELECT id, user_id, job_title, company_name, 
                   LENGTH(content) as content_length, 
                   LEFT(content, 100) as content_preview,
                   language, created_at
            FROM cover_letters 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        letters = cursor.fetchall()
        print(f"\nTotal de cartas encontradas: {len(letters)}")
        
        for letter in letters:
            print(f"\n--- Carta ID: {letter['id']} ---")
            print(f"Usuario: {letter['user_id']}")
            print(f"Puesto: {letter['job_title']}")
            print(f"Empresa: {letter['company_name']}")
            print(f"Idioma: {letter['language']}")
            print(f"Longitud del contenido: {letter['content_length']}")
            print(f"Preview del contenido: {letter['content_preview']}")
            print(f"Fecha: {letter['created_at']}")
    
    cursor.close()
    connection.close()

if __name__ == '__main__':
    debug_cover_letters()