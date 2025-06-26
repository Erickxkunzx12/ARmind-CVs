#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debuggear la consulta de suscripciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

def debug_subscription_query():
    """Debuggear por qué get_user_subscription retorna None"""
    print("🔍 DEBUG: CONSULTA DE SUSCRIPCIONES")
    print("=" * 50)
    
    connection = get_db_connection()
    if not connection:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    cursor = connection.cursor()
    
    # Verificar estructura de tabla subscriptions
    print("\n📋 ESTRUCTURA DE TABLA subscriptions:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'subscriptions'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
    
    # Obtener usuario de prueba
    cursor.execute("SELECT id, email FROM users WHERE email = 'standard@armind.test'")
    user = cursor.fetchone()
    
    if not user:
        print("❌ Usuario de prueba no encontrado")
        return
    
    user_id = user['id']
    print(f"\n👤 Usuario: {user['email']} (ID: {user_id})")
    
    # Verificar datos en tabla subscriptions
    print("\n📊 DATOS EN TABLA subscriptions:")
    cursor.execute("SELECT * FROM subscriptions WHERE user_id = %s", (user_id,))
    subscriptions = cursor.fetchall()
    
    if subscriptions:
        for i, sub in enumerate(subscriptions, 1):
            print(f"\n   Suscripción {i}:")
            for key, value in sub.items():
                print(f"      {key}: {value}")
    else:
        print("   ❌ Sin suscripciones encontradas")
    
    # Probar consulta original
    print("\n🔍 PROBANDO CONSULTA ORIGINAL:")
    try:
        cursor.execute("""
            SELECT s.*, u.current_plan, u.subscription_status, u.subscription_end_date
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.user_id = %s AND s.status = 'active'
            ORDER BY s.created_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            print("   ✅ Consulta exitosa:")
            for key, value in result.items():
                print(f"      {key}: {value}")
        else:
            print("   ❌ Consulta no retornó resultados")
    except Exception as e:
        print(f"   ❌ Error en consulta: {e}")
        
        # Probar consulta alternativa sin created_at
        print("\n🔧 PROBANDO CONSULTA ALTERNATIVA:")
        try:
            cursor.execute("""
                SELECT s.*, u.current_plan, u.subscription_status, u.subscription_end_date
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.user_id = %s AND s.status = 'active'
                ORDER BY s.start_date DESC
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                print("   ✅ Consulta alternativa exitosa:")
                for key, value in result.items():
                    print(f"      {key}: {value}")
            else:
                print("   ❌ Consulta alternativa no retornó resultados")
        except Exception as e2:
            print(f"   ❌ Error en consulta alternativa: {e2}")
    
    # Verificar datos en tabla users
    print("\n👥 DATOS EN TABLA users:")
    cursor.execute("""
        SELECT id, email, current_plan, subscription_status, subscription_end_date
        FROM users 
        WHERE email LIKE '%@armind.test'
    """)
    
    users = cursor.fetchall()
    for user in users:
        print(f"\n   {user['email']}:")
        print(f"      ID: {user['id']}")
        print(f"      current_plan: {user['current_plan']}")
        print(f"      subscription_status: {user['subscription_status']}")
        print(f"      subscription_end_date: {user['subscription_end_date']}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    debug_subscription_query()