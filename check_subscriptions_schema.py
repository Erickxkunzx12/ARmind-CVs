#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el esquema de la tabla subscriptions
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
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

def check_subscriptions_schema():
    """Verificar el esquema de la tabla subscriptions"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Verificar columnas de la tabla subscriptions
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("📋 Columnas de la tabla 'subscriptions':")
        print("=" * 50)
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {col['column_name']}: {col['data_type']} ({nullable})")
        
        # Verificar datos de ejemplo
        print("\n📋 Datos de ejemplo en subscriptions:")
        print("=" * 50)
        cursor.execute("SELECT * FROM subscriptions LIMIT 3")
        sample_data = cursor.fetchall()
        
        if sample_data:
            for i, row in enumerate(sample_data, 1):
                print(f"\nRegistro {i}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")
        else:
            print("No hay datos en la tabla subscriptions")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DEL ESQUEMA DE SUBSCRIPTIONS")
    print("=" * 60)
    check_subscriptions_schema()