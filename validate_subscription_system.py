#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar la implementación completa del sistema de suscripciones y restricciones
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash

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

def check_database_structure():
    """Verificar que todas las tablas necesarias existan"""
    print("\n🔍 Verificando estructura de base de datos...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    required_tables = [
        'users',
        'subscriptions', 
        'usage_tracking',
        'payment_transactions'
    ]
    
    missing_tables = []
    
    for table in required_tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table,))
        
        result = cursor.fetchone()
        exists = result['exists'] if isinstance(result, dict) else result[0]
        if exists:
            print(f"  ✅ Tabla '{table}' existe")
        else:
            print(f"  ❌ Tabla '{table}' NO existe")
            missing_tables.append(table)
    
    cursor.close()
    connection.close()
    
    if missing_tables:
        print(f"\n⚠️  Tablas faltantes: {', '.join(missing_tables)}")
        return False
    
    print("\n✅ Todas las tablas requeridas existen")
    return True

def create_test_users():
    """Crear usuarios de prueba con diferentes planes"""
    print("\n👥 Creando usuarios de prueba...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    test_users = [
        {
            'username': 'admin_test',
            'email': 'admin@armind.test',
            'password': 'admin123',
            'role': 'admin',
            'plan': None  # Los admins no necesitan plan
        },
        {
            'username': 'user_free',
            'email': 'free@armind.test', 
            'password': 'free123',
            'role': 'user',
            'plan': 'free_trial'
        },
        {
            'username': 'user_standard',
            'email': 'standard@armind.test',
            'password': 'standard123', 
            'role': 'user',
            'plan': 'standard'
        },
        {
            'username': 'user_pro',
            'email': 'pro@armind.test',
            'password': 'pro123',
            'role': 'user', 
            'plan': 'pro'
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_data['email'],))
            existing = cursor.fetchone()
            
            if existing:
                print(f"  ⚠️  Usuario {user_data['username']} ya existe (ID: {existing['id']})")
                created_users.append(existing['id'])
                continue
            
            # Crear usuario
            hashed_password = generate_password_hash(user_data['password'])
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, current_plan, subscription_status, subscription_end_date, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_data['username'],
                user_data['email'], 
                hashed_password,
                user_data['role'],
                user_data['plan'],
                'active' if user_data['plan'] else None,
                datetime.now() + timedelta(days=30) if user_data['plan'] else None,
                True  # Marcar usuarios de prueba como verificados
            ))
            
            user_id = cursor.fetchone()['id']
            created_users.append(user_id)
            
            print(f"  ✅ Usuario {user_data['username']} creado (ID: {user_id})")
            
            # Crear suscripción si no es admin
            if user_data['plan']:
                cursor.execute("""
                    INSERT INTO subscriptions (user_id, plan_type, status, start_date, end_date, payment_method, amount, currency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    user_data['plan'],
                    'active',
                    datetime.now(),
                    datetime.now() + timedelta(days=30),
                    'test',
                    0 if user_data['plan'] == 'free_trial' else (10000 if user_data['plan'] == 'standard' else 20000),
                    'CLP'
                ))
                
                subscription_id = cursor.fetchone()['id']
                print(f"    📋 Suscripción {user_data['plan']} creada (ID: {subscription_id})")
                
                # Crear registro de uso inicial
                cursor.execute("""
                    INSERT INTO usage_tracking (user_id, subscription_id, resource_type, used_count, reset_date)
                    VALUES (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                """, (
                    user_id, subscription_id, 'cv_analysis', 0, datetime.now(),
                    user_id, subscription_id, 'cv_creation', 0, datetime.now()
                ))
                
                print(f"    📊 Registro de uso inicializado")
            
        except Exception as e:
            print(f"  ❌ Error creando usuario {user_data['username']}: {e}")
            connection.rollback()
            continue
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print(f"\n✅ Usuarios de prueba configurados: {len(created_users)}")
    return created_users

def test_subscription_restrictions():
    """Probar las restricciones de suscripción"""
    print("\n🧪 Probando restricciones de suscripción...")
    
    # Importar funciones del sistema de suscripción
    try:
        from subscription_system import check_user_limits, get_user_subscription, get_user_usage
        print("  ✅ Módulos de suscripción importados correctamente")
    except ImportError as e:
        print(f"  ❌ Error importando módulos: {e}")
        return False
    
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Obtener usuarios de prueba
    cursor.execute("SELECT id, username, role, current_plan FROM users WHERE email LIKE '%@armind.test'")
    test_users = cursor.fetchall()
    
    for user in test_users:
        print(f"\n  👤 Probando usuario: {user['username']} (Plan: {user['current_plan']})")
        
        # Probar límites de análisis de CV
        can_analyze, msg = check_user_limits(user['id'], 'cv_analysis')
        print(f"    📊 Análisis CV: {'✅ Permitido' if can_analyze else '❌ Bloqueado'} - {msg}")
        
        # Probar límites de creación de CV
        can_create, msg = check_user_limits(user['id'], 'cv_creation')
        print(f"    📝 Creación CV: {'✅ Permitido' if can_create else '❌ Bloqueado'} - {msg}")
        
        # Obtener uso actual
        analysis_usage = get_user_usage(user['id'], 'cv_analysis')
        creation_usage = get_user_usage(user['id'], 'cv_creation')
        print(f"    📈 Uso actual: Análisis={analysis_usage}, Creación={creation_usage}")
    
    cursor.close()
    connection.close()
    
    return True

def check_payment_gateways():
    """Verificar configuración de pasarelas de pago"""
    print("\n💳 Verificando pasarelas de pago...")
    
    # Verificar variables de entorno para Webpay
    webpay_vars = ['WEBPAY_API_KEY', 'WEBPAY_COMMERCE_CODE', 'WEBPAY_ENVIRONMENT']
    webpay_configured = True
    
    for var in webpay_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Configurado")
        else:
            print(f"  ❌ {var}: NO configurado")
            webpay_configured = False
    
    # Verificar variables de entorno para PayPal
    paypal_vars = ['PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET', 'PAYPAL_ENVIRONMENT']
    paypal_configured = True
    
    for var in paypal_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Configurado")
        else:
            print(f"  ❌ {var}: NO configurado")
            paypal_configured = False
    
    if webpay_configured:
        print("  ✅ Webpay: Configuración completa")
    else:
        print("  ⚠️  Webpay: Configuración incompleta")
    
    if paypal_configured:
        print("  ✅ PayPal: Configuración completa")
    else:
        print("  ⚠️  PayPal: Configuración incompleta")
    
    return webpay_configured or paypal_configured

def generate_implementation_report():
    """Generar reporte de implementación"""
    print("\n📋 REPORTE DE IMPLEMENTACIÓN")
    print("=" * 50)
    
    # Verificar estructura
    db_ok = check_database_structure()
    
    # Crear usuarios de prueba
    users_ok = create_test_users()
    
    # Probar restricciones
    restrictions_ok = test_subscription_restrictions()
    
    # Verificar pagos
    payments_ok = check_payment_gateways()
    
    print("\n📊 RESUMEN:")
    print(f"  Base de datos: {'✅ OK' if db_ok else '❌ FALLA'}")
    print(f"  Usuarios de prueba: {'✅ OK' if users_ok else '❌ FALLA'}")
    print(f"  Restricciones: {'✅ OK' if restrictions_ok else '❌ FALLA'}")
    print(f"  Pasarelas de pago: {'✅ OK' if payments_ok else '❌ FALLA'}")
    
    if all([db_ok, users_ok, restrictions_ok, payments_ok]):
        print("\n🎉 SISTEMA COMPLETAMENTE FUNCIONAL")
    else:
        print("\n⚠️  SISTEMA REQUIERE ATENCIÓN")
    
    return all([db_ok, users_ok, restrictions_ok, payments_ok])

if __name__ == "__main__":
    print("🚀 VALIDADOR DEL SISTEMA DE SUSCRIPCIONES ARMind")
    print("=" * 60)
    
    try:
        success = generate_implementation_report()
        
        if success:
            print("\n✅ Validación completada exitosamente")
        else:
            print("\n❌ Se encontraron problemas en la validación")
            
    except Exception as e:
        print(f"\n💥 Error durante la validación: {e}")
        import traceback
        traceback.print_exc()