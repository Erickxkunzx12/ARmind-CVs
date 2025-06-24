#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para simular una actualización de contenido y verificar el problema
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

def test_content_update():
    """Simular actualización de contenido con diferentes usuarios"""
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
        
        print("🧪 Probando actualización de contenido...")
        
        # Obtener usuarios disponibles
        cursor.execute("SELECT id, username, email FROM users ORDER BY id;")
        users = cursor.fetchall()
        print(f"👥 Usuarios disponibles: {len(users)}")
        for user in users:
            print(f"  - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
        
        if not users:
            print("❌ No hay usuarios disponibles")
            return
        
        # Usar el usuario admin (ID 34)
        admin_user = None
        for user in users:
            if user['username'] == 'admin':
                admin_user = user
                break
        
        if not admin_user:
            admin_user = users[0]  # Usar el primer usuario disponible
        
        print(f"\n🔧 Usando usuario: {admin_user['username']} (ID: {admin_user['id']})")
        
        # Simular actualización de analysis_tips
        test_content = {
            'tip_format_title': 'Formato Claro - ACTUALIZADO',
            'tip_format_description': 'Descripción actualizada desde script de prueba',
            'tip_format_icon': 'fas fa-check-circle',
            'tip_format_icon_color': 'text-success'
        }
        
        print("\n📝 Actualizando contenido de analysis_tips...")
        
        for content_key, content_value in test_content.items():
            try:
                # Intentar actualizar primero
                cursor.execute("""
                    UPDATE site_content 
                    SET content_value = %s, updated_at = CURRENT_TIMESTAMP, updated_by = %s 
                    WHERE section = %s AND content_key = %s
                """, (content_value, admin_user['id'], 'analysis_tips', content_key))
                
                if cursor.rowcount == 0:
                    # Si no se actualizó, insertar
                    print(f"  📌 Insertando nuevo registro: {content_key}")
                    cursor.execute("""
                        INSERT INTO site_content (section, content_key, content_value, updated_by) 
                        VALUES (%s, %s, %s, %s)
                    """, ('analysis_tips', content_key, content_value, admin_user['id']))
                else:
                    print(f"  ✅ Actualizado: {content_key}")
                    
            except Exception as e:
                print(f"  ❌ Error con {content_key}: {e}")
                connection.rollback()
                return
        
        connection.commit()
        print("\n✅ Todas las actualizaciones completadas exitosamente")
        
        # Verificar los cambios
        print("\n🔍 Verificando cambios...")
        cursor.execute("""
            SELECT content_key, content_value, updated_by, updated_at 
            FROM site_content 
            WHERE section = 'analysis_tips' 
            ORDER BY content_key
        """)
        
        updated_content = cursor.fetchall()
        for item in updated_content:
            print(f"  - {item['content_key']}: {item['content_value'][:50]}... (por usuario {item['updated_by']})")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Prueba de actualización de contenido")
    print("=" * 50)
    test_content_update()
    print("\n✅ Prueba completada.")