#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la conexión a PostgreSQL
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'cv_analyzer'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def test_postgresql_connection():
    """Probar conexión a PostgreSQL"""
    print("🔍 Probando conexión a PostgreSQL...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"Password: {'***' if DB_CONFIG['password'] else 'NO CONFIGURADA'}")
    print()
    
    try:
        # Intentar conexión
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
        
        print("✅ Conexión a PostgreSQL exitosa!")
        
        # Probar consulta simple
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 Versión de PostgreSQL: {version['version']}")
        
        # Listar todas las tablas existentes
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            table_names = [table['table_name'] for table in tables]
            print(f"📋 Tablas existentes en PostgreSQL: {table_names}")
            
            # Verificar si existe la tabla site_content
            site_content_exists = 'site_content' in table_names
            print(f"📋 Tabla 'site_content' existe: {site_content_exists}")
            
            if site_content_exists:
                # Contar registros en site_content
                cursor.execute("SELECT COUNT(*) FROM site_content;")
                count = cursor.fetchone()[0]
                print(f"📊 Registros en site_content: {count}")
                
                # Mostrar algunos registros de analysis_tips
                cursor.execute("""
                    SELECT section, content_key, content_value 
                    FROM site_content 
                    WHERE section = 'analysis_tips' 
                    LIMIT 5;
                """)
                tips = cursor.fetchall()
                print(f"💡 Consejos de análisis encontrados: {len(tips)}")
                for tip in tips:
                    print(f"  - {tip['content_key']}: {tip['content_value'][:50]}...")
            else:
                print("⚠️ La tabla 'site_content' no existe en PostgreSQL")
                print("💡 Esto explica por qué los cambios no se guardan")
                
        except Exception as table_error:
            print(f"❌ Error consultando tablas: {table_error}")
            print("🔍 Intentando consulta alternativa...")
            
            try:
                cursor.execute("\\dt")
                print("📋 Resultado de \\dt:")
                for row in cursor.fetchall():
                    print(f"  {row}")
            except Exception as dt_error:
                print(f"❌ Error con \\dt: {dt_error}")
        
        cursor.close()
        connection.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verificar que PostgreSQL esté ejecutándose")
        print("2. Verificar las credenciales en el archivo .env")
        print("3. Verificar que la base de datos 'armind_db' exista")
        print("4. Verificar la configuración del firewall")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_sqlite_fallback():
    """Probar si existe un archivo SQLite como fallback"""
    print("\n🔍 Verificando archivos SQLite...")
    sqlite_files = ['cv_analyzer.db', 'armind.db', 'database.db']
    
    for db_file in sqlite_files:
        if os.path.exists(db_file):
            print(f"📁 Encontrado archivo SQLite: {db_file}")
            try:
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"  📋 Tablas: {[table[0] for table in tables]}")
                conn.close()
            except Exception as e:
                print(f"  ❌ Error leyendo SQLite: {e}")
        else:
            print(f"📁 No encontrado: {db_file}")

if __name__ == "__main__":
    print("🚀 Diagnóstico de Base de Datos - ARMind")
    print("=" * 50)
    
    test_postgresql_connection()
    test_sqlite_fallback()
    
    print("\n✅ Diagnóstico completado.")