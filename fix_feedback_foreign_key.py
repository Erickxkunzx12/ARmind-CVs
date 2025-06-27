#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la clave foránea de feedback -> resumes
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

def fix_feedback_foreign_key():
    """Corregir la clave foránea de feedback para permitir eliminación en cascada"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("=== Corrigiendo clave foránea feedback -> resumes ===")
        
        # Verificar la constraint actual
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'feedback' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%resume_id%'
        """)
        
        existing_constraint = cursor.fetchone()
        
        if existing_constraint:
            constraint_name = existing_constraint[0]
            print(f"🔧 Eliminando constraint existente: {constraint_name}")
            cursor.execute(f"ALTER TABLE feedback DROP CONSTRAINT {constraint_name}")
        else:
            print("⚠️  No se encontró constraint existente")
        
        # Crear nueva constraint con ON DELETE CASCADE
        print("✅ Creando nueva constraint con CASCADE")
        cursor.execute("""
            ALTER TABLE feedback 
            ADD CONSTRAINT feedback_resume_id_fkey 
            FOREIGN KEY (resume_id) 
            REFERENCES resumes(id) 
            ON DELETE CASCADE
        """)
        
        # Confirmar cambios
        connection.commit()
        print("✅ Clave foránea de feedback corregida exitosamente")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error corrigiendo clave foránea de feedback: {e}")
        connection.rollback()

def test_user_deletion():
    """Probar eliminación de usuario después de la corrección"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        print("\n=== Probando eliminación de usuario ===")
        
        # Listar usuarios disponibles
        cursor.execute("SELECT id, username, email FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("\nUsuarios disponibles:")
        for user in users:
            print(f"  ID: {user['id']}, Usuario: {user['username']}, Email: {user['email']}")
        
        user_id = input("\nIngresa el ID del usuario a eliminar (o 'q' para salir): ")
        if user_id.lower() == 'q':
            return
        
        user_id = int(user_id)
        
        # Verificar que el usuario existe
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Usuario con ID {user_id} no encontrado")
            return
        
        username = user['username']
        
        # Confirmar eliminación
        confirm = input(f"\n¿Estás seguro de que quieres eliminar al usuario '{username}' (ID: {user_id})? (s/N): ")
        if confirm.lower() != 's':
            print("👋 Eliminación cancelada")
            return
        
        # Intentar eliminar
        print(f"\n🗑️  Eliminando usuario {username} (ID: {user_id})...")
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        if cursor.rowcount > 0:
            connection.commit()
            print(f"✅ Usuario {username} eliminado exitosamente")
            print(f"   Se eliminaron {cursor.rowcount} registro(s)")
        else:
            print(f"⚠️  No se eliminó ningún registro")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error eliminando usuario: {e}")
        connection.rollback()

if __name__ == "__main__":
    print("🔧 Corrección de clave foránea feedback -> resumes")
    
    # Corregir la clave foránea
    fix_feedback_foreign_key()
    
    # Preguntar si quiere probar la eliminación
    test_deletion = input("\n¿Quieres probar la eliminación de usuario ahora? (s/N): ")
    if test_deletion.lower() == 's':
        test_user_deletion()
    else:
        print("👋 Listo. Ahora deberías poder eliminar usuarios desde la interfaz web.")