#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debuggear el error específico de suscripción
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

def debug_get_user_subscription(user_id):
    """Versión de debug de get_user_subscription"""
    print(f"\n🔍 Debuggeando get_user_subscription para user_id: {user_id} (tipo: {type(user_id)})")
    
    connection = get_db_connection()
    if not connection:
        print("❌ No se pudo conectar a la base de datos")
        return None
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Verificar si el usuario existe
        print(f"📋 Verificando si el usuario {user_id} existe...")
        cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"❌ Usuario {user_id} no existe en la base de datos")
            cursor.close()
            connection.close()
            return None
        
        print(f"✅ Usuario encontrado: {user_data['username']} (role: {user_data['role']})")
        
        # Verificar si es administrador
        if user_data['role'] == 'admin':
            print("ℹ️ Usuario es administrador, no necesita suscripción")
            cursor.close()
            connection.close()
            return None
        
        # Buscar suscripción activa
        print(f"📋 Buscando suscripción activa para usuario {user_id}...")
        cursor.execute("""
            SELECT s.id, s.user_id, s.plan_type, s.status, s.start_date, s.end_date, 
                   s.payment_method, s.transaction_id, s.amount, s.currency,
                   s.created_at, s.updated_at,
                   u.current_plan, u.subscription_status, u.subscription_end_date
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.user_id = %s AND s.status = 'active'
            ORDER BY s.start_date DESC
            LIMIT 1
        """, (user_id,))
        
        subscription = cursor.fetchone()
        
        if subscription:
            print(f"✅ Suscripción encontrada: {subscription['plan_type']} (estado: {subscription['status']})")
            print(f"   Inicio: {subscription['start_date']}")
            print(f"   Fin: {subscription['end_date']}")
            
            # Crear el diccionario de respuesta
            result = {
                'id': subscription['id'],
                'user_id': subscription['user_id'],
                'plan_type': subscription['plan_type'],
                'status': subscription['status'],
                'start_date': subscription['start_date'],
                'end_date': subscription['end_date'],
                'payment_method': subscription['payment_method'],
                'transaction_id': subscription['transaction_id'],
                'amount': subscription['amount'],
                'currency': subscription['currency'],
                'created_at': subscription['created_at'],
                'updated_at': subscription['updated_at'],
                'expires_at': subscription['end_date'],
                'current_plan': subscription['current_plan'],
                'subscription_status': subscription['subscription_status'],
                'subscription_end_date': subscription['subscription_end_date']
            }
            
            cursor.close()
            connection.close()
            return result
        else:
            print(f"❌ No se encontró suscripción activa para usuario {user_id}")
            
            # Verificar si hay suscripciones inactivas
            cursor.execute("""
                SELECT s.id, s.plan_type, s.status, s.start_date, s.end_date
                FROM subscriptions s
                WHERE s.user_id = %s
                ORDER BY s.created_at DESC
            """, (user_id,))
            
            all_subs = cursor.fetchall()
            if all_subs:
                print(f"📋 Suscripciones encontradas (todas):")
                for sub in all_subs:
                    print(f"   - {sub['plan_type']} ({sub['status']}) {sub['start_date']} - {sub['end_date']}")
            else:
                print("📋 No hay suscripciones para este usuario")
            
            cursor.close()
            connection.close()
            return None
        
    except Exception as e:
        print(f"❌ Error en get_user_subscription: {e}")
        print(f"   Tipo de error: {type(e)}")
        if connection:
            connection.close()
        return None

def test_all_users():
    """Probar con todos los usuarios de prueba"""
    print("\n🔍 Probando con todos los usuarios de prueba...")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, role FROM users WHERE email LIKE '%@armind.test' ORDER BY id")
        test_users = cursor.fetchall()
        
        print(f"📋 Usuarios de prueba encontrados: {len(test_users)}")
        
        for user in test_users:
            print(f"\n👤 Usuario: {user['username']} ({user['email']}) - ID: {user['id']}")
            result = debug_get_user_subscription(user['id'])
            if result:
                print(f"   ✅ Suscripción: {result['current_plan']}")
            else:
                print(f"   ❌ Sin suscripción")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error probando usuarios: {e}")
        if connection:
            connection.close()

def main():
    """Función principal"""
    print("🔧 DEBUG DE ERRORES DE SUSCRIPCIÓN")
    print("=" * 60)
    
    # Probar con el usuario específico que está causando problemas
    print("\n📋 Probando con usuario ID 38 (que aparece en los logs):")
    debug_get_user_subscription(38)
    
    # Probar con todos los usuarios de prueba
    test_all_users()
    
    print("\n" + "=" * 60)
    print("✅ Debug completado")

if __name__ == "__main__":
    main()