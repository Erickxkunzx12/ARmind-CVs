#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== Prueba de Conexión a SQLite ===")

try:
    # Intentar conexión a SQLite
    print("\n--- Intentando conexión a SQLite ---")
    conn = sqlite3.connect('cv_analyzer.db')
    conn.row_factory = sqlite3.Row
    
    # Verificar si la conexión funciona
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    
    if result and result[0] == 1:
        print("✅ Conexión exitosa a SQLite")
        
        # Verificar si existen tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print("\nTablas existentes:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("\nNo hay tablas en la base de datos.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error conectando a SQLite: {e}")

print("\n=== Recomendación ===")
print("Ya que hay problemas con la conexión a PostgreSQL, puedes:")
print("1. Modificar app_fixed_secure.py para usar SQLite en lugar de PostgreSQL")
print("2. Verificar la instalación de PostgreSQL y sus credenciales")
print("3. Crear un nuevo archivo .env con credenciales correctas")