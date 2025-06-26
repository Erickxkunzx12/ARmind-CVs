#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las correcciones de base de datos
"""

import os
import sys
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
        print(f"❌ Error de conexión: {e}")
        return None

def test_user_loading():
    """Probar la carga de usuarios con la columna correcta"""
    print("\n🔍 Probando carga de usuarios...")
    print("=" * 50)
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Probar la consulta corregida
        cursor.execute("SELECT id, email, username, role FROM users WHERE id = %s", (38,))
        user_data = cursor.fetchone()
        
        if user_data:
            print(f"✅ Usuario cargado correctamente:")
            print(f"   ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Role: {user_data.get('role', 'user')}")
            return True
        else:
            print("❌ No se encontró el usuario")
            return False
            
    except Exception as e:
        print(f"❌ Error probando carga de usuario: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def test_subscription_functions():
    """Probar las funciones de suscripción corregidas"""
    print("\n🔍 Probando funciones de suscripción...")
    print("=" * 50)
    
    # Importar las funciones desde subscription_system
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from subscription_system import get_user_subscription, get_user_usage, check_user_limits
        
        # Probar con usuario de prueba
        test_user_id = 38
        
        print(f"\n📋 Probando get_user_subscription para usuario {test_user_id}:")
        subscription = get_user_subscription(test_user_id)
        if subscription:
            print(f"✅ Suscripción obtenida: {subscription.get('current_plan', 'N/A')}")
        else:
            print("ℹ️ Sin suscripción (normal para usuarios admin)")
        
        print(f"\n📊 Probando get_user_usage para usuario {test_user_id}:")
        usage = get_user_usage(test_user_id, 'cv_analysis')
        print(f"✅ Uso actual: {usage}")
        
        print(f"\n🔒 Probando check_user_limits para usuario {test_user_id}:")
        can_analyze = check_user_limits(test_user_id, 'cv_analysis')
        print(f"✅ Puede analizar CV: {can_analyze}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando funciones de suscripción: {e}")
        return False

def test_database_schema():
    """Verificar el esquema de la base de datos"""
    print("\n🔍 Verificando esquema de base de datos...")
    print("=" * 50)
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar columnas de la tabla users
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("📋 Columnas de la tabla 'users':")
        for col in columns:
            print(f"   - {col['column_name']}: {col['data_type']}")
        
        # Verificar si existe la columna 'username'
        username_exists = any(col['column_name'] == 'username' for col in columns)
        name_exists = any(col['column_name'] == 'name' for col in columns)
        
        print(f"\n✅ Columna 'username' existe: {username_exists}")
        print(f"❌ Columna 'name' existe: {name_exists}")
        
        return username_exists and not name_exists
        
    except Exception as e:
        print(f"❌ Error verificando esquema: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def main():
    """Función principal"""
    print("🔧 PRUEBA DE CORRECCIONES DE BASE DE DATOS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Ejecutar pruebas
    if test_database_schema():
        tests_passed += 1
    
    if test_user_loading():
        tests_passed += 1
    
    if test_subscription_functions():
        tests_passed += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN: {tests_passed}/{total_tests} pruebas pasaron")
    
    if tests_passed == total_tests:
        print("✅ Todas las correcciones funcionan correctamente")
        print("\n🚀 La aplicación debería funcionar sin errores de base de datos")
    else:
        print("❌ Algunas pruebas fallaron, revisar los errores")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)