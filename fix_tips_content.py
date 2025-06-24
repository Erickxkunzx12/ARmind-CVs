#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir el contenido de los consejos de análisis
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

def fix_tips_content():
    """Corregir el contenido de los consejos de análisis"""
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
        
        print("🔧 Corrigiendo contenido de consejos de análisis...")
        
        # Contenido correcto para los consejos
        correct_content = {
            'tip_format_title': 'Formato Claro',
            'tip_format_description': 'Asegúrate de que tu CV tenga un formato limpio y sea fácil de leer.',
            'tip_format_icon': 'fas fa-file-alt',
            'tip_format_icon_color': 'text-success',
            
            'tip_keywords_title': 'Palabras Clave',
            'tip_keywords_description': 'Incluye palabras clave relevantes para tu industria y puesto objetivo.',
            'tip_keywords_icon': 'fas fa-key',
            'tip_keywords_icon_color': 'text-primary',
            
            'tip_achievements_title': 'Logros Cuantificados',
            'tip_achievements_description': 'Usa números y porcentajes para demostrar tus logros.',
            'tip_achievements_icon': 'fas fa-chart-bar',
            'tip_achievements_icon_color': 'text-info',
            
            'tip_errors_title': 'Sin Errores',
            'tip_errors_description': 'Revisa la ortografía y gramática antes de subir tu CV.',
            'tip_errors_icon': 'fas fa-spell-check',
            'tip_errors_icon_color': 'text-warning'
        }
        
        # Obtener un usuario válido para updated_by
        cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        if not admin_user:
            cursor.execute("SELECT id FROM users LIMIT 1")
            admin_user = cursor.fetchone()
        
        user_id = admin_user['id']
        print(f"📝 Usando usuario ID: {user_id}")
        
        # Actualizar cada elemento
        for content_key, content_value in correct_content.items():
            try:
                # Intentar actualizar primero
                cursor.execute("""
                    UPDATE site_content 
                    SET content_value = %s, updated_at = CURRENT_TIMESTAMP, updated_by = %s 
                    WHERE section = %s AND content_key = %s
                """, (content_value, user_id, 'analysis_tips', content_key))
                
                if cursor.rowcount == 0:
                    # Si no se actualizó, insertar
                    print(f"  📌 Insertando: {content_key}")
                    cursor.execute("""
                        INSERT INTO site_content (section, content_key, content_value, updated_by) 
                        VALUES (%s, %s, %s, %s)
                    """, ('analysis_tips', content_key, content_value, user_id))
                else:
                    print(f"  ✅ Actualizado: {content_key}")
                    
            except Exception as e:
                print(f"  ❌ Error con {content_key}: {e}")
                connection.rollback()
                return
        
        connection.commit()
        print("\n✅ Todos los consejos han sido corregidos exitosamente")
        
        # Verificar los cambios
        print("\n🔍 Verificando cambios...")
        cursor.execute("""
            SELECT content_key, content_value 
            FROM site_content 
            WHERE section = 'analysis_tips' 
            ORDER BY content_key
        """)
        
        updated_content = cursor.fetchall()
        for item in updated_content:
            print(f"  - {item['content_key']}: {item['content_value']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Corrección de contenido de consejos de análisis")
    print("=" * 60)
    fix_tips_content()
    print("\n✅ Corrección completada.")