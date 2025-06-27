#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debuggear el problema de eliminación de usuarios
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'armind_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def check_user_dependencies(user_id):
    """Verificar qué dependencias tiene un usuario"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        print(f"\n=== Verificando dependencias para usuario ID: {user_id} ===")
        
        # Verificar si el usuario existe
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"❌ Usuario {user_id} no existe")
            return
        
        print(f"✅ Usuario encontrado: {user['username']} ({user['email']})")
        print(f"   Rol: {user['role']}")
        print(f"   Baneado: {user['is_banned']}")
        
        # Verificar tablas relacionadas
        tables_to_check = [
            ('resumes', 'user_id'),
            ('user_cvs', 'user_id'),
            ('user_subscriptions', 'user_id'),
            ('subscription_history', 'user_id'),
            ('coupon_usage', 'user_id'),
            ('user_sessions', 'user_id')
        ]
        
        # Verificar feedback indirectamente a través de resumes
        try:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM feedback f 
                JOIN resumes r ON f.resume_id = r.id 
                WHERE r.user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            count = result['count'] if result else 0
            print(f"   feedback (via resumes): {count} registros")
        except Exception as e:
            print(f"   feedback (via resumes): Error verificando - {e}")
        
        for table, column in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE {column} = %s", (user_id,))
                result = cursor.fetchone()
                count = result['count'] if result else 0
                print(f"   {table}: {count} registros")
            except Exception as e:
                print(f"   {table}: Error verificando - {e}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error verificando dependencias: {e}")

def test_delete_user(user_id):
    """Probar eliminación de usuario"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print(f"\n=== Intentando eliminar usuario ID: {user_id} ===")
        
        # Intentar eliminar
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        rows_affected = cursor.rowcount
        
        print(f"Filas afectadas: {rows_affected}")
        
        if rows_affected > 0:
            print("✅ Usuario eliminado exitosamente")
            connection.commit()
        else:
            print("❌ No se pudo eliminar el usuario")
            connection.rollback()
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error eliminando usuario: {e}")
        connection.rollback()

def list_users():
    """Listar usuarios disponibles"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, username, email, role, is_banned, created_at 
            FROM users 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        print("\n=== Lista de usuarios ===")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Rol':<10} {'Baneado':<8}")
        print("-" * 80)
        
        for user in users:
            print(f"{user['id']:<5} {user['username']:<20} {user['email']:<30} {user['role']:<10} {user['is_banned']:<8}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error listando usuarios: {e}")

if __name__ == "__main__":
    print("🔍 Debug de eliminación de usuarios")
    
    # Listar usuarios
    list_users()
    
    # Solicitar ID de usuario para verificar
    try:
        user_id = input("\nIngresa el ID del usuario a verificar (o 'q' para salir): ")
        if user_id.lower() == 'q':
            exit()
        
        user_id = int(user_id)
        
        # Verificar dependencias
        check_user_dependencies(user_id)
        
        # Preguntar si quiere intentar eliminar
        confirm = input(f"\n¿Quieres intentar eliminar el usuario {user_id}? (s/N): ")
        if confirm.lower() == 's':
            test_delete_user(user_id)
        
    except ValueError:
        print("❌ ID de usuario inválido")
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")