#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== Prueba Simple de Conexión a PostgreSQL ===")

# Intentar con contraseña hardcodeada simple
try:
    print("\n--- Intentando conexión con contraseña hardcodeada ---")
    conn = psycopg2.connect(
        host="localhost",
        database="cv_analyzer",
        user="postgres",
        password="postgres",  # Contraseña simple sin caracteres especiales
        port="5432"
    )
    print("✅ Conexión exitosa con contraseña hardcodeada")
    conn.close()
    
except Exception as e:
    print(f"❌ Error con contraseña hardcodeada: {e}")
    
    # Si falla, intentar con contraseña del .env pero sin client_encoding
    try:
        print("\n--- Intentando conexión con contraseña del .env sin encoding ---")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'cv_analyzer'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("✅ Conexión exitosa con contraseña del .env sin encoding")
        conn.close()
        
    except Exception as e2:
        print(f"❌ Error con contraseña del .env sin encoding: {e2}")
        
        print("\n🔍 Diagnóstico:")
        print("- Verifica que PostgreSQL esté ejecutándose")
        print("- Verifica que la base de datos 'cv_analyzer' exista")
        print("- Verifica que el usuario 'postgres' tenga acceso")
        print("- Intenta cambiar la contraseña de PostgreSQL a una sin caracteres especiales")