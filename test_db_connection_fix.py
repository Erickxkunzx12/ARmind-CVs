#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== Prueba de Conexión a Base de Datos ===")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_PASSWORD: {'*' * len(os.getenv('DB_PASSWORD', ''))}")

try:
    # Intentar conexión con diferentes configuraciones de codificación
    print("\n--- Intentando conexión con client_encoding='utf8' ---")
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'cv_analyzer'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432'),
        client_encoding='utf8'
    )
    print("✅ Conexión exitosa con utf8")
    conn.close()
    
except Exception as e:
    print(f"❌ Error con utf8: {e}")
    
    try:
        print("\n--- Intentando conexión con client_encoding='latin1' ---")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'cv_analyzer'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432'),
            client_encoding='latin1'
        )
        print("✅ Conexión exitosa con latin1")
        conn.close()
        
    except Exception as e2:
        print(f"❌ Error con latin1: {e2}")
        
        try:
            print("\n--- Intentando conexión sin client_encoding ---")
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'cv_analyzer'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            print("✅ Conexión exitosa sin client_encoding")
            conn.close()
            
        except Exception as e3:
            print(f"❌ Error sin client_encoding: {e3}")
            print("\n🔍 Diagnóstico:")
            print("- Verifica que PostgreSQL esté ejecutándose")
            print("- Verifica las credenciales en el archivo .env")
            print("- Verifica que la base de datos 'cv_analyzer' exista")
            print("- El problema puede estar en caracteres especiales en la contraseña")