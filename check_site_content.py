#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el contenido de la tabla site_content
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

def check_site_content():
    """Verificar contenido de la tabla site_content"""
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
        
        print("🔍 Verificando tabla site_content...")
        
        # Verificar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'site_content' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("📋 Estructura de la tabla:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) as total FROM site_content;")
        total = cursor.fetchone()['total']
        print(f"\n📊 Total de registros: {total}")
        
        # Contar por sección
        cursor.execute("""
            SELECT section, COUNT(*) as count 
            FROM site_content 
            GROUP BY section 
            ORDER BY section;
        """)
        sections = cursor.fetchall()
        print("\n📊 Registros por sección:")
        for section in sections:
            print(f"  - {section['section']}: {section['count']}")
        
        # Mostrar registros de analysis_tips
        cursor.execute("""
            SELECT content_key, content_value 
            FROM site_content 
            WHERE section = 'analysis_tips' 
            ORDER BY content_key;
        """)
        tips = cursor.fetchall()
        print(f"\n💡 Consejos de análisis ({len(tips)} encontrados):")
        for tip in tips:
            value_preview = tip['content_value'][:50] + '...' if len(tip['content_value']) > 50 else tip['content_value']
            print(f"  - {tip['content_key']}: {value_preview}")
        
        # Insertar un registro de prueba
        print("\n🧪 Probando inserción...")
        try:
            cursor.execute("""
                INSERT INTO site_content (section, content_key, content_value, updated_by) 
                VALUES (%s, %s, %s, %s)
            """, ('test', 'test_key', 'test_value', 1))
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
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Verificación de site_content")
    print("=" * 40)
    check_site_content()
    print("\n✅ Verificación completada.")