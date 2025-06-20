#!/usr/bin/env python3
"""
Script para agregar la restricción única compuesta a la tabla site_content
"""

import psycopg2
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()

def fix_site_content_constraint():
    """Agregar restricción única compuesta (section, content_key) a site_content"""
    try:
        # Conectar a la base de datos
        db_config = config_manager.get_database_config()
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        print("Conectado a la base de datos...")
        
        # Primero, eliminar la restricción única existente en 'section' si existe
        try:
            cursor.execute("ALTER TABLE site_content DROP CONSTRAINT IF EXISTS site_content_section_key")
            print("Restricción única anterior eliminada (si existía)")
        except Exception as e:
            print(f"No se pudo eliminar restricción anterior: {e}")
        
        # Agregar la nueva restricción única compuesta
        try:
            cursor.execute("""
                ALTER TABLE site_content 
                ADD CONSTRAINT site_content_section_content_key_unique 
                UNIQUE (section, content_key)
            """)
            print("Nueva restricción única compuesta agregada exitosamente")
        except psycopg2.errors.UniqueViolation as e:
            print(f"Error: Ya existen datos duplicados que violan la restricción única: {e}")
            # Mostrar los duplicados
            cursor.execute("""
                SELECT section, content_key, COUNT(*) 
                FROM site_content 
                GROUP BY section, content_key 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print("Registros duplicados encontrados:")
                for section, content_key, count in duplicates:
                    print(f"  - {section}.{content_key}: {count} registros")
            return False
        except Exception as e:
            print(f"Error agregando restricción: {e}")
            return False
        
        # Confirmar cambios
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

if __name__ == "__main__":
    fix_site_content_constraint()