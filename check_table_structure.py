#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import RealDictCursor
from database_config import DB_CONFIG
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_users_table():
    """Verificar la estructura de la tabla users"""
    try:
        # Conectar a la base de datos PostgreSQL
        print("Conectando a la base de datos PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar si la tabla users existe
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print("\n✅ Estructura de la tabla 'users':")
            print("-" * 50)
            for col in columns:
                print(f"  {col['column_name']:<20} {col['data_type']:<15} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        else:
            print("❌ La tabla 'users' no existe o no tiene columnas.")
        
        # Verificar todas las tablas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Tablas existentes en la base de datos:")
        print("-" * 40)
        for table in tables:
            print(f"  - {table['table_name']}")
        
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"Error general: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("    VERIFICADOR DE ESTRUCTURA DE TABLA - ARMIND")
    print("=" * 60)
    print()
    
    check_users_table()
    print("\n" + "=" * 60)