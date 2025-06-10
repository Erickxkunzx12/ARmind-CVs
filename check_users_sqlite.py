#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_users():
    db_path = 'cv_analyzer.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ La tabla 'users' no existe en la base de datos")
            conn.close()
            return
        
        # Obtener todos los usuarios
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        
        print(f"📊 Usuarios encontrados: {len(users)}")
        print("=" * 50)
        
        if users:
            for user in users:
                print(f"ID: {user[0]}")
                print(f"Username: {user[1]}")
                print(f"Email: {user[2]}")
                print(f"Verified: {'Sí' if user[4] else 'No'}")
                print(f"Created: {user[6]}")
                print("-" * 30)
        else:
            print("❌ No hay usuarios registrados en la base de datos")
            print("\n💡 Sugerencias:")
            print("1. Registra un nuevo usuario desde la página de registro")
            print("2. Verifica que la aplicación esté usando la base de datos correcta")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al consultar la base de datos: {e}")

if __name__ == '__main__':
    check_users()