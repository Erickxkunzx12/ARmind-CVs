#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar usuarios existentes y probar inserción en site_content
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

def check_users_and_test_insert():
    """Verificar usuarios y probar inserción en site_content"""
    try:
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
        
        cursor = connection.cursor()
        
        print("👥 Verificando usuarios existentes...")
        
        # Verificar usuarios
        cursor.execute("SELECT id, username, email FROM users ORDER BY id LIMIT 10;")
        users = cursor.fetchall()
        print(f"📊 Usuarios encontrados: {len(users)}")
        for user in users:
            print(f"  - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
        
        if users:
            # Usar el primer usuario para la prueba
            test_user_id = users[0]['id']
            print(f"\n🧪 Probando inserción con usuario ID: {test_user_id}")
            
            try:
                cursor.execute("""
                    INSERT INTO site_content (section, content_key, content_value, updated_by) 
                    VALUES (%s, %s, %s, %s)
                """, ('test', 'test_key', 'test_value', test_user_id))
                connection.commit()
                print("✅ Inserción exitosa")
                
                # Eliminar el registro de prueba
                cursor.execute("""
                    DELETE FROM site_content 
                    WHERE section = 'test' AND content_key = 'test_key'
                """)
                connection.commit()
                print("✅ Eliminación exitosa")
                
            except Exception as insert_error:
                print(f"❌ Error en inserción: {insert_error}")
                connection.rollback()
        else:
            print("❌ No se encontraron usuarios. Creando usuario de prueba...")
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash) 
                    VALUES (%s, %s, %s) RETURNING id
                """, ('admin', 'admin@example.com', 'dummy_hash'))
                new_user_id = cursor.fetchone()['id']
                connection.commit()
                print(f"✅ Usuario creado con ID: {new_user_id}")
                
                # Probar inserción con el nuevo usuario
                cursor.execute("""
                    INSERT INTO site_content (section, content_key, content_value, updated_by) 
                    VALUES (%s, %s, %s, %s)
                """, ('test', 'test_key', 'test_value', new_user_id))
                connection.commit()
                print("✅ Inserción exitosa con nuevo usuario")
                
                # Eliminar el registro de prueba
                cursor.execute("""
                    DELETE FROM site_content 
                    WHERE section = 'test' AND content_key = 'test_key'
                """)
                connection.commit()
                print("✅ Eliminación exitosa")
                
            except Exception as create_error:
                print(f"❌ Error creando usuario: {create_error}")
                connection.rollback()
        
        # Verificar la restricción de clave foránea
        print("\n🔍 Verificando restricciones de clave foránea...")
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='site_content';
        """)
        constraints = cursor.fetchall()
        print("📋 Restricciones de clave foránea:")
        for constraint in constraints:
            print(f"  - {constraint['constraint_name']}: {constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Verificación de usuarios y site_content")
    print("=" * 50)
    check_users_and_test_insert()
    print("\n✅ Verificación completada.")