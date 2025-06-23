
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración final - Cambiar a nueva arquitectura
Generado automáticamente el 2025-06-23 14:50:21
"""

import os
import shutil
import sys

def migrate_to_new_architecture():
    """Migrar a la nueva arquitectura"""
    print("🚀 Iniciando migración a nueva arquitectura...")
    
    # Renombrar app.py actual
    if os.path.exists('app.py'):
        shutil.move('app.py', 'app_legacy.py')
        print("📦 app.py renombrado a app_legacy.py")
    
    # Activar nueva aplicación
    if os.path.exists('app_new.py'):
        shutil.move('app_new.py', 'app.py')
        print("✅ app_new.py activado como app.py")
    
    # Crear archivo .env de ejemplo si no existe
    if not os.path.exists('.env'):
        env_content = """# Configuración de base de datos
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cv_analyzer
DB_USER=root
DB_PASSWORD=

# APIs de IA (configurar según disponibilidad)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Configuración de aplicación
SECRET_KEY=change-this-in-production
DEBUG=true
ENVIRONMENT=development

# Configuración de archivos
MAX_FILE_SIZE_MB=10
UPLOAD_FOLDER=uploads
"""
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("📄 Archivo .env de ejemplo creado")
    
    print("🎉 Migración completada exitosamente!")
    print("")
    print("📋 Próximos pasos:")
    print("1. Configurar las variables en el archivo .env")
    print("2. Ejecutar: python app.py")
    print("3. La aplicación legacy está disponible en app_legacy.py")
    print("4. Los backups están disponibles en las carpetas backup_*")

if __name__ == '__main__':
    migrate_to_new_architecture()
