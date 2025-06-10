#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar la función de conexión desde app.py
from app import get_db_connection

def fix_database():
    """Agregar columna keywords a la tabla feedback si no existe"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Verificar si la columna keywords existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'feedback' AND column_name = 'keywords'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                # Agregar la columna keywords si no existe
                cursor.execute("ALTER TABLE feedback ADD COLUMN keywords TEXT")
                connection.commit()
                print("Columna 'keywords' agregada exitosamente a la tabla feedback")
            else:
                print("La columna 'keywords' ya existe en la tabla feedback")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"Error al modificar la base de datos: {e}")
            if connection:
                connection.close()
    else:
        print("No se pudo conectar a la base de datos")

if __name__ == "__main__":
    fix_database()