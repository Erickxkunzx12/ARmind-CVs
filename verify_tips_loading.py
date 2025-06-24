#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar cómo se cargan los consejos de análisis
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

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        return psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def simulate_tips_loading():
    """Simular exactamente cómo la aplicación carga los consejos"""
    print("🔍 Simulando carga de consejos como en la aplicación...")
    
    # Valores por defecto (como en la aplicación)
    tips_data = {
        'tip_format': {
            'title': 'Formato Claro',
            'description': 'Asegúrate de que tu CV tenga un formato limpio y sea fácil de leer.',
            'icon': 'fas fa-file-alt',
            'icon_color': 'text-success'
        }
    }
    
    print("📋 Valores por defecto cargados")
    
    # Intentar cargar desde base de datos
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            print("\n🔍 Consultando base de datos...")
            
            # Obtener todos los consejos de análisis desde la base de datos
            cursor.execute("""
                SELECT content_key, content_value 
                FROM site_content 
                WHERE section = 'analysis_tips'
                ORDER BY content_key
            """)
            
            results = cursor.fetchall()
            analysis_tips = {}
            for row in results:
                analysis_tips[row['content_key']] = row['content_value']
            
            print(f"📊 Datos encontrados en BD: {len(analysis_tips)} elementos")
            for key, value in analysis_tips.items():
                print(f"  - {key}: {value[:50]}...")
            
            # Sobrescribir valores por defecto con los de la base de datos si existen
            if analysis_tips:
                print("\n🔄 Sobrescribiendo valores por defecto...")
                
                if 'tip_format_title' in analysis_tips:
                    old_title = tips_data['tip_format']['title']
                    tips_data['tip_format']['title'] = analysis_tips['tip_format_title']
                    print(f"    ✅ Título actualizado: {old_title} -> {tips_data['tip_format']['title']}")
                
                if 'tip_format_description' in analysis_tips:
                    old_desc = tips_data['tip_format']['description'][:30]
                    tips_data['tip_format']['description'] = analysis_tips['tip_format_description']
                    new_desc = tips_data['tip_format']['description'][:30]
                    print(f"    ✅ Descripción actualizada: {old_desc}... -> {new_desc}...")
                
                print(f"\n✅ Consejos cargados desde BD: {len(analysis_tips)} elementos")
            else:
                print("\n⚠️  No hay consejos personalizados en BD, usando valores por defecto")
            
            cursor.close()
            connection.close()
    except Exception as e:
        print(f"\n❌ Error cargando desde BD, usando valores por defecto: {e}")
    
    print("\n📋 Valores finales:")
    print(f"  - tip_format: {tips_data['tip_format']['title']} | {tips_data['tip_format']['description'][:50]}...")
    
    print("\n✅ Consejos de análisis cargados correctamente")
    return tips_data

if __name__ == "__main__":
    print("🚀 Verificación de carga de consejos de análisis")
    print("=" * 60)
    simulate_tips_loading()
    print("\n✅ Verificación completada.")