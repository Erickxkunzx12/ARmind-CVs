#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la visualización de suscripciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from subscription_system import get_user_subscription, SUBSCRIPTION_PLANS
from app import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

def test_user_subscription_display():
    """Probar cómo se muestran las suscripciones para cada usuario"""
    print("🧪 PRUEBA DE VISUALIZACIÓN DE SUSCRIPCIONES")
    print("=" * 50)
    
    # Usuarios de prueba
    test_emails = [
        'admin@armind.test',
        'free@armind.test', 
        'standard@armind.test',
        'pro@armind.test'
    ]
    
    connection = get_db_connection()
    if not connection:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    cursor = connection.cursor()
    
    for email in test_emails:
        print(f"\n👤 USUARIO: {email}")
        print("-" * 40)
        
        # Obtener ID del usuario
        cursor.execute("SELECT id, role, current_plan FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print("❌ Usuario no encontrado")
            continue
        
        user_id = user['id']
        user_role = user['role']
        current_plan = user['current_plan']
        
        print(f"   ID: {user_id}")
        print(f"   Rol: {user_role}")
        print(f"   Plan actual: {current_plan}")
        
        # Probar función get_user_subscription
        subscription = get_user_subscription(user_id)
        
        print(f"\n📋 RESULTADO get_user_subscription():")
        if subscription:
            print(f"   ✅ Suscripción encontrada:")
            print(f"      - Plan: {subscription.get('plan_type', 'N/A')}")
            print(f"      - Estado: {subscription.get('status', 'N/A')}")
            print(f"      - Inicio: {subscription.get('start_date', 'N/A')}")
            print(f"      - Fin: {subscription.get('end_date', 'N/A')}")
            
            # Verificar si el plan existe en SUBSCRIPTION_PLANS
            plan_type = subscription.get('plan_type')
            if plan_type in SUBSCRIPTION_PLANS:
                plan_info = SUBSCRIPTION_PLANS[plan_type]
                print(f"      - Nombre del plan: {plan_info['name']}")
                print(f"      - Límites: {plan_info['limits']}")
            else:
                print(f"      ❌ Plan '{plan_type}' no encontrado en SUBSCRIPTION_PLANS")
        else:
            print(f"   ❌ Sin suscripción (retorna None)")
            
            # Para administradores, verificar si esto es esperado
            if user_role == 'admin':
                print(f"      ℹ️  Esto es normal para administradores")
            else:
                print(f"      ⚠️  Usuario normal sin suscripción - esto puede ser un problema")
        
        # Verificar directamente en la tabla subscriptions
        cursor.execute("""
            SELECT plan_type, status, start_date, end_date 
            FROM subscriptions 
            WHERE user_id = %s AND status = 'active'
            ORDER BY start_date DESC
            LIMIT 1
        """, (user_id,))
        
        direct_sub = cursor.fetchone()
        
        print(f"\n🔍 CONSULTA DIRECTA subscriptions:")
        if direct_sub:
            print(f"   ✅ Suscripción activa encontrada:")
            print(f"      - Plan: {direct_sub['plan_type']}")
            print(f"      - Estado: {direct_sub['status']}")
            print(f"      - Inicio: {direct_sub['start_date']}")
            print(f"      - Fin: {direct_sub['end_date']}")
        else:
            print(f"   ❌ Sin suscripción activa en tabla subscriptions")
    
    cursor.close()
    connection.close()
    
    # Mostrar planes disponibles
    print(f"\n📊 PLANES DISPONIBLES EN SUBSCRIPTION_PLANS:")
    print("-" * 50)
    for plan_key, plan_info in SUBSCRIPTION_PLANS.items():
        print(f"   {plan_key}: {plan_info['name']}")
        print(f"      - Precio: ${plan_info['price']} {plan_info['currency']}")
        print(f"      - Límites: {plan_info['limits']}")
        print()

def test_template_context():
    """Simular el contexto que se pasa al template"""
    print(f"\n🎭 SIMULACIÓN DE CONTEXTO DE TEMPLATE")
    print("=" * 50)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Probar con usuario estándar
    cursor.execute("SELECT id FROM users WHERE email = 'standard@armind.test'")
    user = cursor.fetchone()
    
    if user:
        user_id = user['id']
        user_subscription = get_user_subscription(user_id)
        
        print(f"Usuario ID: {user_id}")
        print(f"user_subscription: {user_subscription}")
        print(f"subscription_plans: {SUBSCRIPTION_PLANS}")
        
        if user_subscription:
            plan_type = user_subscription.get('plan_type')
            if plan_type in SUBSCRIPTION_PLANS:
                plan_name = SUBSCRIPTION_PLANS[plan_type]['name']
                print(f"\n✅ Template debería mostrar: {plan_name}")
                print(f"   Acceso a: subscription_plans['{plan_type}']['name']")
            else:
                print(f"\n❌ Error: plan_type '{plan_type}' no existe en SUBSCRIPTION_PLANS")
        else:
            print(f"\n❌ Error: user_subscription es None")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    test_user_subscription_display()
    test_template_context()