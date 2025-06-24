#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para investigar la estructura exacta de los datos SQL
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

def investigate_sql_structure():
    """Investigar la estructura exacta de los datos devueltos"""
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
        
        print("🔍 Investigando estructura de datos SQL...")
        print("=" * 50)
        
        # Ejecutar la consulta exacta
        cursor.execute("""
            SELECT content_key, content_value 
            FROM site_content 
            WHERE section = 'analysis_tips'
        """)
        
        results = cursor.fetchall()
        
        print(f"📊 Total de resultados: {len(results)}")
        print(f"📊 Tipo de results: {type(results)}")
        
        if results:
            print("\n🔍 Analizando cada fila:")
            for i, row in enumerate(results):
                print(f"\n--- Fila {i+1} ---")
                print(f"Tipo de fila: {type(row)}")
                print(f"Contenido completo: {row}")
                
                if hasattr(row, 'keys'):
                    print(f"Claves disponibles: {list(row.keys())}")
                
                try:
                    print(f"row[0]: {row[0]}")
                except Exception as e:
                    print(f"Error accediendo row[0]: {e}")
                
                try:
                    print(f"row[1]: {row[1]}")
                except Exception as e:
                    print(f"Error accediendo row[1]: {e}")
                
                # Si es un RealDictRow, intentar acceso por nombre
                try:
                    print(f"row['content_key']: {row['content_key']}")
                    print(f"row['content_value']: {row['content_value']}")
                except Exception as e:
                    print(f"Error accediendo por nombre: {e}")
                
                # Limitar a las primeras 3 filas para no saturar
                if i >= 2:
                    print("\n... (mostrando solo las primeras 3 filas)")
                    break
        
        else:
            print("❌ No se encontraron resultados")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_sql_structure()