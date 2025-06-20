#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()

# Cargar variables de entorno
load_dotenv()

def create_admin_user():
    """Crear usuario administrador en la base de datos PostgreSQL"""
    
    try:
        # Conectar a la base de datos PostgreSQL
        print("Conectando a la base de datos PostgreSQL...")
        db_config = config_manager.get_database_config()
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar si la tabla users existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        
        result = cursor.fetchone()
        table_exists = result['exists']
        if not table_exists:
            print("Error: La tabla 'users' no existe en la base de datos.")
            print("Por favor, ejecuta la aplicación primero para inicializar las tablas.")
            conn.close()
            return False
        
        # Verificar si ya existe un usuario admin
        cursor.execute("SELECT id FROM users WHERE username = %s", ('admin',))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print("Ya existe un usuario administrador. Actualizando...")
            cursor.execute("""
                UPDATE users 
                SET email = %s, password_hash = %s, role = %s, email_verified = %s
                WHERE username = %s
            """, (
                'admin@armind.com',
                generate_password_hash('admin123'),
                'admin',
                True,
                'admin'
            ))
        else:
            print("Creando nuevo usuario administrador...")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                'admin',
                'admin@armind.com',
                generate_password_hash('admin123'),
                'admin',
                True,
                datetime.now()
            ))
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print("\n✅ Usuario administrador creado/actualizado exitosamente:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   Email: admin@armind.com")
        print("   Rol: admin")
        print("\n🔗 Puedes acceder al panel de administración en:")
        print("   http://127.0.0.1:5000/login")
        print("\n📝 Después de iniciar sesión, serás redirigido automáticamente al panel de administración.")
        
        return True
        
    except psycopg2.Error as e:
        print(f"Error de PostgreSQL: {e}")
        print(f"Código de error: {e.pgcode}")
        print(f"Detalles: {e.pgerror}")
        return False
    except Exception as e:
        print(f"Error general: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("    CREADOR DE USUARIO ADMINISTRADOR - ARMIND")
    print("=" * 60)
    print()
    
    success = create_admin_user()
    
    if success:
        print("\n✅ Proceso completado exitosamente.")
    else:
        print("\n❌ Error en el proceso. Verifica que la aplicación esté ejecutándose.")
    
    print("\n" + "=" * 60)