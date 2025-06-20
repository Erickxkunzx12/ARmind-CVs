#!/usr/bin/env python3
"""
Script de migración de SQLite a PostgreSQL
Este script migra todos los datos de la base de datos SQLite existente a PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()
import sys

def connect_sqlite():
    """Conectar a la base de datos SQLite"""
    try:
        conn = sqlite3.connect('cv_analyzer.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error conectando a SQLite: {e}")
        return None

def connect_postgresql():
    """Conectar a la base de datos PostgreSQL"""
    try:
        db_config = config_manager.get_database_config()
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port'],
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None

def migrate_table(sqlite_conn, pg_conn, table_name, columns):
    """Migrar una tabla específica"""
    try:
        # Leer datos de SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"No hay datos en la tabla {table_name}")
            return True
        
        # Insertar en PostgreSQL
        pg_cursor = pg_conn.cursor()
        
        # Construir query de inserción
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insertar cada fila
        for row in rows:
            values = [row[col] for col in columns]
            pg_cursor.execute(insert_query, values)
        
        pg_conn.commit()
        print(f"Migrados {len(rows)} registros de la tabla {table_name}")
        return True
        
    except Exception as e:
        print(f"Error migrando tabla {table_name}: {e}")
        pg_conn.rollback()
        return False

def main():
    """Función principal de migración"""
    print("Iniciando migración de SQLite a PostgreSQL...")
    
    # Conectar a ambas bases de datos
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        print("No se pudo conectar a SQLite")
        return False
    
    pg_conn = connect_postgresql()
    if not pg_conn:
        print("No se pudo conectar a PostgreSQL")
        sqlite_conn.close()
        return False
    
    try:
        # Definir las tablas y sus columnas (excluyendo id para SERIAL)
        tables_to_migrate = {
            'users': ['username', 'email', 'password_hash', 'created_at'],
            'resumes': ['user_id', 'filename', 'content', 'created_at'],
            'jobs': ['title', 'company', 'location', 'description', 'url', 'source', 'created_at'],
            'feedback': ['resume_id', 'score', 'strengths', 'weaknesses', 'recommendations', 'created_at']
        }
        
        # Migrar cada tabla
        success = True
        for table_name, columns in tables_to_migrate.items():
            if not migrate_table(sqlite_conn, pg_conn, table_name, columns):
                success = False
                break
        
        if success:
            print("\n¡Migración completada exitosamente!")
            print("Puedes ahora usar PostgreSQL como tu base de datos.")
        else:
            print("\nLa migración falló. Revisa los errores anteriores.")
        
        return success
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        return False
    
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)