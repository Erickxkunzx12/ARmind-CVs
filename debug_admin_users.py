#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'armind_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        port=os.getenv('DB_PORT', '5432')
    )

def check_admin_users():
    """Verificar usuarios administradores en la base de datos"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Obtener todos los usuarios
        cursor.execute("""
            SELECT id, username, email, role, created_at
            FROM users 
            ORDER BY role DESC, created_at ASC
        """)
        
        users = cursor.fetchall()
        
        print("=== USUARIOS EN LA BASE DE DATOS ===")
        print(f"Total de usuarios: {len(users)}")
        print()
        
        admin_count = 0
        for user in users:
            role_display = user['role'] or 'user'
            status = []
            
            # Verificar si hay columnas adicionales disponibles
            # status se mantiene vacío por ahora
            
            status_str = f" ({', '.join(status)})" if status else ""
            
            print(f"ID: {user['id']} | Usuario: {user['username']} | Email: {user['email']}")
            print(f"Rol: {role_display}{status_str}")
            print(f"Creado: {user['created_at']}")
            print("-" * 60)
            
            if user['role'] == 'admin':
                admin_count += 1
        
        print(f"\n=== RESUMEN ===")
        print(f"Administradores encontrados: {admin_count}")
        
        if admin_count == 0:
            print("\n⚠️  NO HAY USUARIOS ADMINISTRADORES")
            print("Para crear un administrador, ejecuta:")
            print("UPDATE users SET role = 'admin' WHERE email = 'tu_email@ejemplo.com';")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error al verificar usuarios: {e}")

if __name__ == "__main__":
    check_admin_users()