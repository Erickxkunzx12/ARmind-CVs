#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== Prueba Simple de Conexión a PostgreSQL ===")

def test_basic_connection():
    """Prueba de conexión básica con credenciales simples"""
    try:
        print("Probando conexión básica...")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'cv_analyzer'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("✅ Conexión exitosa con credenciales básicas")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error con credenciales básicas: {e}")
        return False

def test_env_connection():
    """Prueba de conexión usando variables de entorno"""
    try:
        print("Probando conexión con variables de entorno...")
        
        # Check if required environment variables are set
        required_vars = ['DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Variables de entorno faltantes: {missing_vars}")
            return False
            
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'cv_analyzer'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("✅ Conexión exitosa con variables de entorno")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con variables de entorno: {e}")
        return False

def main():
    """Función principal para ejecutar las pruebas"""
    print("\n--- Prueba 1: Conexión básica ---")
    basic_success = test_basic_connection()
    
    print("\n--- Prueba 2: Conexión con variables de entorno ---")
    env_success = test_env_connection()
    
    if not basic_success and not env_success:
        print("\n🔍 Diagnóstico:")
        print("- Verifica que PostgreSQL esté ejecutándose")
        print("- Verifica que la base de datos 'cv_analyzer' exista")
        print("- Verifica que el usuario 'postgres' tenga acceso")
        print("- Configura las variables de entorno en el archivo .env")
        
if __name__ == "__main__":
    main()