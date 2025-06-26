#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado de los planes de suscripción de los usuarios
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
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
            cursor_factory=RealDictCursor,
            client_encoding='utf8'
        )
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def check_users_and_plans():
    """Verificar usuarios y sus planes"""
    print("🔍 Verificando usuarios y planes de suscripción...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar usuarios de prueba
        print("\n👥 USUARIOS DE PRUEBA:")
        print("=" * 60)
        
        cursor.execute("""
            SELECT id, username, email, role, current_plan, subscription_status, subscription_end_date
            FROM users 
            WHERE email LIKE '%@armind.test'
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ No se encontraron usuarios de prueba")
            return False
        
        for user in users:
            print(f"\n📧 {user['email']}")
            print(f"   ID: {user['id']}")
            print(f"   Usuario: {user['username']}")
            print(f"   Rol: {user['role']}")
            print(f"   Plan actual: {user['current_plan']}")
            print(f"   Estado suscripción: {user['subscription_status']}")
            print(f"   Fecha fin: {user['subscription_end_date']}")
            
            # Verificar suscripciones en tabla subscriptions
            cursor.execute("""
                SELECT id, plan_type, status, start_date, end_date, amount, currency
                FROM subscriptions 
                WHERE user_id = %s
                ORDER BY start_date DESC
            """, (user['id'],))
            
            subscriptions = cursor.fetchall()
            
            if subscriptions:
                print(f"   📋 Suscripciones ({len(subscriptions)}):")
                for sub in subscriptions:
                    print(f"      - ID: {sub['id']}, Plan: {sub['plan_type']}, Estado: {sub['status']}")
                    print(f"        Inicio: {sub['start_date']}, Fin: {sub['end_date']}")
                    print(f"        Monto: {sub['amount']} {sub['currency']}")
            else:
                print("   ❌ Sin suscripciones en tabla subscriptions")
            
            # Verificar uso de recursos
            cursor.execute("""
                SELECT resource_type, used_count, reset_date
                FROM usage_tracking 
                WHERE user_id = %s
            """, (user['id'],))
            
            usage = cursor.fetchall()
            
            if usage:
                print(f"   📊 Uso de recursos:")
                for u in usage:
                    print(f"      - {u['resource_type']}: {u['used_count']} (reset: {u['reset_date']})")
            else:
                print("   ❌ Sin registro de uso")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando usuarios: {e}")
        return False

def fix_missing_plans():
    """Corregir usuarios sin planes asignados"""
    print("\n🔧 Corrigiendo usuarios sin planes...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Usuarios que deberían tener planes pero no los tienen
        users_to_fix = [
            {'email': 'free@armind.test', 'plan': 'free_trial'},
            {'email': 'standard@armind.test', 'plan': 'standard'},
            {'email': 'pro@armind.test', 'plan': 'pro'}
        ]
        
        for user_data in users_to_fix:
            # Verificar si el usuario existe y no tiene plan
            cursor.execute("""
                SELECT id, current_plan 
                FROM users 
                WHERE email = %s
            """, (user_data['email'],))
            
            user = cursor.fetchone()
            
            if not user:
                print(f"❌ Usuario {user_data['email']} no encontrado")
                continue
            
            user_id = user['id']
            
            # Verificar si ya tiene suscripción activa
            cursor.execute("""
                SELECT id FROM subscriptions 
                WHERE user_id = %s AND status = 'active'
            """, (user_id,))
            
            existing_sub = cursor.fetchone()
            
            if existing_sub:
                print(f"✅ Usuario {user_data['email']} ya tiene suscripción activa")
                continue
            
            # Actualizar plan en tabla users
            cursor.execute("""
                UPDATE users 
                SET current_plan = %s, 
                    subscription_status = 'active',
                    subscription_end_date = NOW() + INTERVAL '30 days'
                WHERE id = %s
            """, (user_data['plan'], user_id))
            
            # Crear suscripción
            amount = 0 if user_data['plan'] == 'free_trial' else (10000 if user_data['plan'] == 'standard' else 20000)
            
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan_type, status, start_date, end_date, payment_method, amount, currency)
                VALUES (%s, %s, 'active', NOW(), NOW() + INTERVAL '30 days', 'test', %s, 'CLP')
                RETURNING id
            """, (user_id, user_data['plan'], amount))
            
            subscription_id = cursor.fetchone()['id']
            
            # Crear registro de uso inicial
            cursor.execute("""
                INSERT INTO usage_tracking (user_id, subscription_id, resource_type, used_count, reset_date)
                VALUES (%s, %s, 'cv_analysis', 0, NOW()),
                       (%s, %s, 'cv_creation', 0, NOW())
                ON CONFLICT (user_id, resource_type) DO NOTHING
            """, (user_id, subscription_id, user_id, subscription_id))
            
            print(f"✅ Plan {user_data['plan']} asignado a {user_data['email']} (Sub ID: {subscription_id})")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✅ Corrección completada")
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo planes: {e}")
        connection.rollback()
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE PLANES DE SUSCRIPCIÓN")
    print("=" * 50)
    
    # Verificar estado actual
    if check_users_and_plans():
        # Preguntar si se quiere corregir
        print("\n¿Deseas corregir los usuarios sin planes? (s/n): ", end="")
        response = input().lower().strip()
        
        if response in ['s', 'si', 'y', 'yes']:
            fix_missing_plans()
            print("\n🔍 Verificando estado después de la corrección...")
            check_users_and_plans()
        else:
            print("\n✅ Diagnóstico completado sin cambios")
    else:
        print("\n❌ Error en el diagnóstico")