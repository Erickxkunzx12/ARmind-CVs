#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la función get_user_subscription
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection
from psycopg2.extras import RealDictCursor

def test_get_user_subscription_fixed():
    """Versión corregida de get_user_subscription"""
    def get_user_subscription_fixed(user_id):
        """Obtener la suscripción activa del usuario - VERSIÓN CORREGIDA"""
        connection = get_db_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            
            # Primero verificar si es administrador
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user_role = cursor.fetchone()
            
            if user_role and user_role[0] == 'admin':
                # Los administradores no necesitan suscripción, tienen acceso completo
                cursor.close()
                connection.close()
                return None
            
            # Para usuarios normales, buscar en la tabla subscriptions
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
            cursor.close()
            connection.close()
            
            if subscription:
                # Convertir a diccionario para compatibilidad
                return {
                    'id': subscription[0],
                    'user_id': subscription[1],
                    'plan_type': subscription[2],
                    'status': subscription[3],
                    'start_date': subscription[4],
                    'end_date': subscription[5],
                    'payment_method': subscription[6],
                    'transaction_id': subscription[7],
                    'amount': subscription[8],
                    'currency': subscription[9],
                    'created_at': subscription[10],
                    'updated_at': subscription[11],
                    'expires_at': subscription[5],  # Alias para compatibilidad con templates
                    'current_plan': subscription[12],
                    'subscription_status': subscription[13],
                    'subscription_end_date': subscription[14]
                }
            
            return None
            
        except Exception as e:
            print(f"Error al obtener suscripción del usuario: {e}")
            if connection:
                connection.close()
            return None
    
    # Probar con usuarios de prueba
    print("🧪 PROBANDO FUNCIÓN CORREGIDA")
    print("=" * 50)
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    test_emails = ['free@armind.test', 'standard@armind.test', 'pro@armind.test']
    
    for email in test_emails:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            print(f"\n👤 {email} (ID: {user_id})")
            
            subscription = get_user_subscription_fixed(user_id)
            
            if subscription:
                print(f"   ✅ Suscripción encontrada:")
                print(f"      Plan: {subscription['plan_type']}")
                print(f"      Estado: {subscription['status']}")
                print(f"      Inicio: {subscription['start_date']}")
                print(f"      Fin: {subscription['end_date']}")
                print(f"      Expires_at: {subscription['expires_at']}")
            else:
                print(f"   ❌ Sin suscripción")
    
    cursor.close()
    connection.close()

def create_fixed_subscription_system():
    """Crear archivo con función corregida"""
    print("\n🔧 CREANDO VERSIÓN CORREGIDA DE subscription_system.py")
    
    # Leer archivo original
    with open('subscription_system.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Función corregida
    new_function = '''def get_user_subscription(user_id):
    """Obtener la suscripción activa del usuario"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Primero verificar si es administrador
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()
        
        if user_role and user_role[0] == 'admin':
            # Los administradores no necesitan suscripción, tienen acceso completo
            cursor.close()
            connection.close()
            return None
        
        # Para usuarios normales, buscar en la tabla subscriptions
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
        cursor.close()
        connection.close()
        
        if subscription:
            # Convertir a diccionario para compatibilidad con templates
            return {
                'id': subscription[0],
                'user_id': subscription[1],
                'plan_type': subscription[2],
                'status': subscription[3],
                'start_date': subscription[4],
                'end_date': subscription[5],
                'payment_method': subscription[6],
                'transaction_id': subscription[7],
                'amount': subscription[8],
                'currency': subscription[9],
                'created_at': subscription[10],
                'updated_at': subscription[11],
                'expires_at': subscription[5],  # Alias para compatibilidad con templates
                'current_plan': subscription[12],
                'subscription_status': subscription[13],
                'subscription_end_date': subscription[14]
            }
        
        return None
        
    except Exception as e:
        print(f"Error al obtener suscripción del usuario: {e}")
        if connection:
            connection.close()
        return None'''
    
    # Buscar y reemplazar la función original
    import re
    
    # Patrón para encontrar la función get_user_subscription
    pattern = r'def get_user_subscription\(user_id\):.*?(?=\ndef |\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        
        # Crear backup
        with open('subscription_system_backup.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Escribir versión corregida
        with open('subscription_system.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("   ✅ Función get_user_subscription corregida")
        print("   📋 Backup creado: subscription_system_backup.py")
        return True
    else:
        print("   ❌ No se pudo encontrar la función para reemplazar")
        return False

if __name__ == "__main__":
    # Primero probar la función corregida
    test_get_user_subscription_fixed()
    
    # Preguntar si aplicar la corrección
    print("\n¿Aplicar la corrección al archivo subscription_system.py? (s/n): ", end="")
    response = input().lower().strip()
    
    if response in ['s', 'si', 'y', 'yes']:
        if create_fixed_subscription_system():
            print("\n✅ Corrección aplicada exitosamente")
            print("\n🔄 Probando función corregida...")
            # Recargar módulo y probar
            import importlib
            import subscription_system
            importlib.reload(subscription_system)
            
            from subscription_system import get_user_subscription
            
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE email = 'standard@armind.test'")
            user = cursor.fetchone()
            
            if user:
                result = get_user_subscription(user[0])
                if result:
                    print(f"   ✅ Función corregida funciona: Plan {result['plan_type']}")
                else:
                    print(f"   ❌ Función corregida aún no funciona")
            
            cursor.close()
            connection.close()
        else:
            print("\n❌ Error aplicando la corrección")
    else:
        print("\n✅ Corrección no aplicada")