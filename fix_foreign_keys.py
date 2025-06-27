#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir las claves foráneas y permitir eliminación en cascada
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

def check_foreign_keys():
    """Verificar las claves foráneas existentes"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        print("=== Verificando claves foráneas ===")
        
        # Consultar todas las claves foráneas que referencian la tabla users
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                tc.constraint_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
            JOIN information_schema.key_column_usage AS referenced_kcu
                ON rc.unique_constraint_name = referenced_kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND referenced_kcu.table_name = 'users'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        foreign_keys = cursor.fetchall()
        
        for fk in foreign_keys:
            print(f"Tabla: {fk['table_name']}, Columna: {fk['column_name']}, Constraint: {fk['constraint_name']}, Delete Rule: {fk['delete_rule']}")
        
        cursor.close()
        connection.close()
        
        return foreign_keys
        
    except Exception as e:
        print(f"Error verificando claves foráneas: {e}")
        return []

def fix_foreign_keys():
    """Corregir las claves foráneas para permitir eliminación en cascada"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("\n=== Corrigiendo claves foráneas ===")
        
        # Lista de tablas y sus claves foráneas que necesitan ser corregidas
        tables_to_fix = [
            ('resumes', 'user_id', 'resumes_user_id_fkey'),
            ('user_cvs', 'user_id', 'user_cvs_user_id_fkey'),
            ('user_subscriptions', 'user_id', 'user_subscriptions_user_id_fkey'),
            ('subscription_history', 'user_id', 'subscription_history_user_id_fkey'),
            ('coupon_usage', 'user_id', 'coupon_usage_user_id_fkey'),
            ('user_sessions', 'user_id', 'user_sessions_user_id_fkey')
        ]
        
        for table_name, column_name, constraint_name in tables_to_fix:
            try:
                print(f"\nProcesando tabla: {table_name}")
                
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table_name,))
                
                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    print(f"  ⚠️  Tabla {table_name} no existe, saltando...")
                    continue
                
                # Verificar si la constraint existe
                cursor.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = %s 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE %s
                """, (table_name, f"%{column_name}%"))
                
                existing_constraint = cursor.fetchone()
                
                if existing_constraint:
                    actual_constraint_name = existing_constraint[0]
                    print(f"  🔧 Eliminando constraint existente: {actual_constraint_name}")
                    cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT {actual_constraint_name}")
                
                # Crear nueva constraint con ON DELETE CASCADE
                print(f"  ✅ Creando nueva constraint con CASCADE")
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    FOREIGN KEY ({column_name}) 
                    REFERENCES users(id) 
                    ON DELETE CASCADE
                """)
                
                print(f"  ✅ Constraint {constraint_name} creada exitosamente")
                
            except Exception as e:
                print(f"  ❌ Error procesando {table_name}: {e}")
                # Continuar con la siguiente tabla
                continue
        
        # Confirmar cambios
        connection.commit()
        print("\n✅ Todas las claves foráneas han sido corregidas")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error corrigiendo claves foráneas: {e}")
        connection.rollback()

def test_delete_after_fix():
    """Probar eliminación después de la corrección"""
    print("\n=== Probando eliminación después de la corrección ===")
    
    # Importar y usar la función de debug
    from debug_delete_user import list_users, check_user_dependencies
    
    list_users()
    
    try:
        user_id = input("\nIngresa el ID del usuario a probar (o 'q' para salir): ")
        if user_id.lower() == 'q':
            return
        
        user_id = int(user_id)
        check_user_dependencies(user_id)
        
    except ValueError:
        print("❌ ID de usuario inválido")
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")

if __name__ == "__main__":
    print("🔧 Corrección de claves foráneas para eliminación de usuarios")
    
    # Verificar estado actual
    print("\n1. Verificando estado actual...")
    foreign_keys = check_foreign_keys()
    
    # Preguntar si quiere proceder con la corrección
    if foreign_keys:
        proceed = input("\n¿Quieres proceder con la corrección de claves foráneas? (s/N): ")
        if proceed.lower() == 's':
            fix_foreign_keys()
            
            # Verificar nuevamente
            print("\n2. Verificando después de la corrección...")
            check_foreign_keys()
            
            # Probar eliminación
            test_after = input("\n¿Quieres probar la eliminación ahora? (s/N): ")
            if test_after.lower() == 's':
                test_delete_after_fix()
        else:
            print("👋 Operación cancelada")
    else:
        print("✅ No se encontraron claves foráneas para corregir")