#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def update_connection_encoding(file_path, encoding='LATIN1'):
    """Actualiza la configuración de codificación en la conexión a PostgreSQL"""
    if not os.path.exists(file_path):
        print(f"❌ El archivo {file_path} no existe")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Buscar la función get_db_connection
        if 'get_db_connection' in content:
            # Verificar si ya tiene client_encoding
            if 'client_encoding' in content:
                # Reemplazar la codificación existente
                modified_content = re.sub(
                    r"client_encoding=['\"]\w+['\"]?", 
                    f"client_encoding='{encoding}'", 
                    content
                )
            else:
                # Añadir client_encoding a la conexión
                modified_content = content.replace(
                    "connection = psycopg2.connect(", 
                    f"connection = psycopg2.connect(\n            client_encoding='{encoding}',"
                )
                
                # Si no encuentra el patrón anterior, intentar con otro formato común
                if modified_content == content:
                    modified_content = content.replace(
                        "conn = psycopg2.connect(", 
                        f"conn = psycopg2.connect(\n        client_encoding='{encoding}',"
                    )
            
            # Guardar el archivo modificado
            if modified_content != content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                print(f"✅ Archivo {file_path} actualizado para usar codificación {encoding}")
                return True
            else:
                print(f"⚠️ No se pudo modificar la configuración de codificación en {file_path}")
                return False
        else:
            print(f"⚠️ No se encontró la función get_db_connection en {file_path}")
            return False
    
    except Exception as e:
        print(f"❌ Error al actualizar el archivo: {e}")
        return False

def main():
    print("="*50)
    print("🔧 CORRECCIÓN DE CODIFICACIÓN POSTGRESQL")
    print("="*50)
    
    # Archivos a modificar
    files_to_update = [
        'app_fixed_secure.py',
        'app.py'
    ]
    
    # Codificaciones a probar
    encodings = ['LATIN1', 'SQL_ASCII', 'UTF8']
    
    # Preguntar qué codificación usar
    print("\nSelecciona la codificación a utilizar:")
    for i, enc in enumerate(encodings, 1):
        print(f"{i}. {enc}")
    
    try:
        choice = int(input("\nIngresa el número de la codificación (1-3): "))
        if 1 <= choice <= len(encodings):
            selected_encoding = encodings[choice-1]
        else:
            print("⚠️ Opción inválida, usando LATIN1 por defecto")
            selected_encoding = 'LATIN1'
    except ValueError:
        print("⚠️ Entrada inválida, usando LATIN1 por defecto")
        selected_encoding = 'LATIN1'
    
    print(f"\n🔄 Aplicando codificación {selected_encoding} a los archivos...")
    
    # Actualizar cada archivo
    success_count = 0
    for file in files_to_update:
        if update_connection_encoding(file, selected_encoding):
            success_count += 1
    
    # Mostrar resumen
    if success_count == len(files_to_update):
        print(f"\n✅ Todos los archivos ({success_count}/{len(files_to_update)}) fueron actualizados correctamente")
    elif success_count > 0:
        print(f"\n⚠️ {success_count}/{len(files_to_update)} archivos fueron actualizados")
    else:
        print("\n❌ No se pudo actualizar ningún archivo")
    
    print("\n🚀 Instrucciones para probar la aplicación:")
    print("1. Ejecuta: python app_fixed_secure.py")
    print("2. Accede a: http://127.0.0.1:5000")
    print("3. Si sigue fallando, prueba con otra codificación")

if __name__ == "__main__":
    main()