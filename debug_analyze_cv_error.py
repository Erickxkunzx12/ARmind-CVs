#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para diagnosticar el error específico en analyze_cv
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
    """Función idéntica a la de app.py"""
    try:
        # Usar opciones adicionales para manejar problemas de codificación
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor,
            client_encoding='UTF8',
            options="-c client_encoding=UTF8"
        )
        
        return connection
    except psycopg2.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None
    except Exception as err:
        print(f"Error inesperado de base de datos: {err}")
        return None

def debug_analyze_cv_tips_loading():
    """Simular exactamente la carga de consejos como en analyze_cv"""
    print("🔍 Diagnosticando error en analyze_cv...")
    print("=" * 50)
    
    # Definir consejos de análisis con valores por defecto (como en app.py)
    tips_data = {
        'tip_format': {
            'title': 'Formato Claro',
            'description': 'Asegúrate de que tu CV tenga un formato limpio y sea fácil de leer.',
            'icon': 'fas fa-check-circle',
            'icon_color': 'text-success'
        },
        'tip_keywords': {
            'title': 'Palabras Clave',
            'description': 'Incluye palabras clave relevantes para tu industria y puesto objetivo.',
            'icon': 'fas fa-key',
            'icon_color': 'text-primary'
        },
        'tip_achievements': {
            'title': 'Logros Cuantificados',
            'description': 'Usa números y porcentajes para demostrar tus logros.',
            'icon': 'fas fa-chart-bar',
            'icon_color': 'text-info'
        },
        'tip_errors': {
            'title': 'Sin Errores',
            'description': 'Revisa la ortografía y gramática antes de subir tu CV.',
            'icon': 'fas fa-spell-check',
            'icon_color': 'text-warning'
        }
    }
    
    print("📋 Valores por defecto definidos")
    
    # Intentar cargar desde base de datos (código exacto de app.py)
    try:
        print("🔗 Intentando obtener conexión...")
        connection = get_db_connection()
        
        if connection:
            print("✅ Conexión obtenida exitosamente")
            cursor = connection.cursor()
            
            print("📊 Ejecutando consulta SQL...")
            # Obtener todos los consejos de análisis desde la base de datos
            cursor.execute("""
                SELECT content_key, content_value 
                FROM site_content 
                WHERE section = 'analysis_tips'
            """)
            
            print("📥 Obteniendo resultados...")
            results = cursor.fetchall()
            analysis_tips = {}
            for row in results:
                analysis_tips[row[0]] = row[1]
            
            print(f"📊 Resultados obtenidos: {len(analysis_tips)} elementos")
            
            # Sobrescribir valores por defecto con los de la base de datos si existen
            if analysis_tips:
                print("🔄 Sobrescribiendo valores por defecto...")
                for tip_type in ['tip_format', 'tip_keywords', 'tip_achievements', 'tip_errors']:
                    if f'{tip_type}_title' in analysis_tips:
                        tips_data[tip_type]['title'] = analysis_tips[f'{tip_type}_title']
                        print(f"  ✅ {tip_type}_title actualizado")
                    if f'{tip_type}_description' in analysis_tips:
                        tips_data[tip_type]['description'] = analysis_tips[f'{tip_type}_description']
                        print(f"  ✅ {tip_type}_description actualizado")
                    if f'{tip_type}_icon' in analysis_tips:
                        tips_data[tip_type]['icon'] = analysis_tips[f'{tip_type}_icon']
                        print(f"  ✅ {tip_type}_icon actualizado")
                    if f'{tip_type}_icon_color' in analysis_tips:
                        tips_data[tip_type]['icon_color'] = analysis_tips[f'{tip_type}_icon_color']
                        print(f"  ✅ {tip_type}_icon_color actualizado")
                
                print(f"✅ Consejos cargados desde BD: {len(analysis_tips)} elementos")
            else:
                print("⚠️ No hay consejos personalizados en BD, usando valores por defecto")
            
            print("🔒 Cerrando cursor y conexión...")
            cursor.close()
            connection.close()
            print("✅ Recursos liberados correctamente")
            
        else:
            print("❌ No se pudo obtener conexión a la base de datos")
            
    except Exception as e:
        print(f"❌ Error cargando desde BD, usando valores por defecto: {e}")
        print(f"📋 Tipo de error: {type(e).__name__}")
        import traceback
        print(f"📋 Traceback completo:")
        traceback.print_exc()
    
    print("\n✅ Consejos de análisis cargados correctamente")
    
    # Mostrar estado final
    print("\n📋 Estado final de tips_data:")
    for tip_type, data in tips_data.items():
        print(f"  - {tip_type}: {data['title']} | {data['description'][:50]}...")

if __name__ == "__main__":
    debug_analyze_cv_tips_loading()