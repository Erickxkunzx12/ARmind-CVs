#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_resumes_table():
    """Verificar estructura de la tabla resumes"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        cur = conn.cursor()
        
        print("=" * 60)
        print("    VERIFICANDO TABLA RESUMES")
        print("=" * 60)
        
        # Verificar columnas de la tabla resumes
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'resumes' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        if columns:
            print("\n✅ Columnas en tabla 'resumes':")
            print("-" * 50)
            for col in columns:
                print(f"  {col[0]:<20} {col[1]:<20} {col[2]}")
        else:
            print("❌ No se encontraron columnas en la tabla 'resumes'")
        
        # Verificar todas las tablas que contienen 'resume' o 'cv'
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%resume%' OR table_name LIKE '%cv%')
            ORDER BY table_name;
        """)
        
        print("\n📋 Tablas relacionadas con CV/Resume:")
        print("-" * 40)
        tables = cur.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
            
            # Mostrar columnas de cada tabla relacionada
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position;
            """, (table[0],))
            
            table_columns = cur.fetchall()
            for tcol in table_columns:
                print(f"    * {tcol[0]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_resumes_table()