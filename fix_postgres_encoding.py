#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos desde .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'cv_analyzer'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432')
}

def test_connection(encoding=None, show_details=False):
    """Prueba la conexión a PostgreSQL con diferentes configuraciones de codificación"""
    conn_params = DB_CONFIG.copy()
    
    if encoding:
        conn_params['client_encoding'] = encoding
    
    try:
        print(f"\n🔄 Intentando conexión con {'client_encoding=' + encoding if encoding else 'configuración predeterminada'}")
        
        # Mostrar detalles de conexión si se solicita
        if show_details:
            print("\nDetalles de conexión:")
            # Ocultar contraseña en la salida
            safe_params = conn_params.copy()
            safe_params['password'] = '********'
            for key, value in safe_params.items():
                print(f"  {key}: {value}")
        
        # Intentar conexión
        conn = psycopg2.connect(**conn_params)
        
        # Verificar la codificación actual
        cursor = conn.cursor()
        cursor.execute("SHOW client_encoding;")
        current_encoding = cursor.fetchone()[0]
        cursor.execute("SHOW server_encoding;")
        server_encoding = cursor.fetchone()[0]
        
        print(f"✅ Conexión exitosa")
        print(f"📋 Codificación del cliente: {current_encoding}")
        print(f"📋 Codificación del servidor: {server_encoding}")
        
        # Verificar si existen las tablas necesarias
        cursor.execute("""SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'""")
        tables = cursor.fetchall()
        print(f"\n📊 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def fix_encoding_issues():
    """Intenta corregir problemas de codificación en PostgreSQL"""
    print("\n🔧 Intentando corregir problemas de codificación...")
    
    # 1. Intentar con diferentes codificaciones
    encodings = ['UTF8', 'LATIN1', 'SQL_ASCII']
    success = False
    working_encoding = None
    
    for encoding in encodings:
        if test_connection(encoding):
            success = True
            working_encoding = encoding
            break
    
    if not success:
        print("\n❌ No se pudo conectar con ninguna codificación estándar.")
        print("\n🔍 Diagnóstico:")
        print("1. Es posible que la contraseña contenga caracteres especiales que causan problemas.")
        print("2. Puede haber un problema con la configuración del servidor PostgreSQL.")
        print("3. La base de datos podría no existir o el usuario no tiene permisos suficientes.")
        
        # Sugerir soluciones
        print("\n💡 Soluciones recomendadas:")
        print("1. Cambiar la contraseña de PostgreSQL a una sin caracteres especiales:")
        print("   - Ejecuta en una terminal: psql -U postgres")
        print("   - Dentro de psql ejecuta: ALTER USER postgres WITH PASSWORD 'nueva_contraseña';")
        print("   - Actualiza el archivo .env con la nueva contraseña")
        print("2. Verificar que la base de datos existe:")
        print("   - Ejecuta en una terminal: psql -U postgres -c '\\l'")
        print("   - Si no existe, créala con: CREATE DATABASE cv_analyzer;")
        print("3. Verificar la configuración de codificación del servidor PostgreSQL:")
        print("   - Ejecuta: psql -U postgres -c 'SHOW server_encoding;'")
        return False
    
    # Si encontramos una codificación que funciona, actualizar app_fixed_secure.py
    print(f"\n✅ Se encontró una codificación que funciona: {working_encoding}")
    print("\n🔄 Actualizando archivos de la aplicación...")
    
    try:
        # Actualizar app_fixed_secure.py
        update_app_file('app_fixed_secure.py', working_encoding)
        
        # Actualizar app.py
        update_app_file('app.py', working_encoding)
        
        # Actualizar job_search_service.py
        update_app_file('job_search_service.py', working_encoding)
        
        print("\n✅ Archivos actualizados correctamente")
        print(f"\n🚀 La aplicación ahora debería funcionar con PostgreSQL usando codificación {working_encoding}")
        return True
    except Exception as e:
        print(f"\n❌ Error al actualizar archivos: {e}")
        return False

def update_app_file(filename, encoding):
    """Actualiza el archivo de la aplicación para usar la codificación correcta"""
    if not os.path.exists(filename):
        print(f"❌ El archivo {filename} no existe")
        return
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar la función get_db_connection y actualizar la codificación
    if 'get_db_connection' in content:
        # Si ya tiene client_encoding, actualizar el valor
        if 'client_encoding' in content:
            import re
            content = re.sub(r"client_encoding=['\"]\w+['\"]?", f"client_encoding='{encoding}'" , content)
        else:
            # Si no tiene client_encoding, añadirlo a la conexión
            content = content.replace(
                "conn = psycopg2.connect(", 
                f"conn = psycopg2.connect(\n        client_encoding='{encoding}',"
            )
        
        # Guardar el archivo actualizado
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"✅ Archivo {filename} actualizado para usar codificación {encoding}")
    else:
        print(f"⚠️ No se encontró la función get_db_connection en {filename}")

def create_test_database():
    """Crea la base de datos y tablas necesarias si no existen"""
    try:
        # Primero conectar a postgres para verificar si existe la base de datos
        conn_params = DB_CONFIG.copy()
        conn_params['database'] = 'postgres'
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar si existe la base de datos
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"\n🔄 Creando base de datos {DB_CONFIG['database']}...")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"✅ Base de datos {DB_CONFIG['database']} creada correctamente")
        else:
            print(f"✅ La base de datos {DB_CONFIG['database']} ya existe")
        
        conn.close()
        
        # Conectar a la base de datos creada y crear tablas
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla de usuarios si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Crear tabla de análisis de CV si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            filename VARCHAR(200) NOT NULL,
            original_text TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Crear tabla de búsquedas de trabajo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_searches (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            query VARCHAR(200) NOT NULL,
            results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Tablas creadas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")
        return False

def main():
    print("="*50)
    print("🔍 DIAGNÓSTICO Y CORRECCIÓN DE POSTGRESQL")
    print("="*50)
    
    # Mostrar configuración actual
    print("\n📋 Configuración actual:")
    safe_config = DB_CONFIG.copy()
    safe_config['password'] = '********'
    for key, value in safe_config.items():
        print(f"  {key}: {value}")
    
    # Probar conexión con configuración actual
    print("\n🔄 Probando conexión con configuración actual...")
    if test_connection(show_details=True):
        print("\n✅ La conexión a PostgreSQL funciona correctamente")
        
        # Preguntar si desea crear las tablas
        create_tables = input("\n¿Desea crear las tablas necesarias? (s/n): ").lower() == 's'
        if create_tables:
            create_test_database()
    else:
        print("\n❌ La conexión a PostgreSQL falló con la configuración actual")
        
        # Preguntar si desea intentar corregir los problemas
        fix_issues = input("\n¿Desea intentar corregir los problemas de codificación? (s/n): ").lower() == 's'
        if fix_issues:
            if fix_encoding_issues():
                # Si se corrigieron los problemas, preguntar si desea crear las tablas
                create_tables = input("\n¿Desea crear las tablas necesarias? (s/n): ").lower() == 's'
                if create_tables:
                    create_test_database()
        else:
            print("\n⚠️ No se realizaron cambios")
    
    print("\n🏁 Proceso finalizado")

if __name__ == "__main__":
    main()