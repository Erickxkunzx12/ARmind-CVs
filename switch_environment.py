#!/usr/bin/env python3
"""
Cambiador de Entorno - ARMind
Script para cambiar fácilmente entre entornos de desarrollo.
"""

import os
import sys
import shutil
from pathlib import Path

def switch_environment(target_env):
    """Cambiar al entorno especificado"""
    
    environments = ['development', 'production', 'testing']
    
    if target_env not in environments:
        print(f"❌ Entorno inválido. Opciones: {', '.join(environments)}")
        return False
    
    env_file = f'.env.{target_env}'
    
    if not os.path.exists(env_file):
        print(f"❌ Archivo {env_file} no encontrado")
        return False
    
    # Backup del .env actual si existe
    if os.path.exists('.env'):
        backup_file = '.env.backup'
        shutil.copy('.env', backup_file)
        print(f"📄 Backup creado: {backup_file}")
    
    # Copiar configuración del entorno
    shutil.copy(env_file, '.env')
    
    # Establecer variable de entorno
    os.environ['FLASK_ENV'] = target_env
    
    print(f"✅ Cambiado a entorno: {target_env}")
    print(f"📄 Configuración activa: {env_file} -> .env")
    
    # Validar configuración
    try:
        from config import validate_current_config
        validate_current_config()
    except ImportError:
        print("⚠️ No se pudo validar la configuración")
    
    return True

def show_current_environment():
    """Mostrar entorno actual"""
    current_env = os.getenv('FLASK_ENV', 'development')
    print(f"🔧 Entorno actual: {current_env}")
    
    if os.path.exists('.env'):
        print("📄 Archivo .env activo")
    else:
        print("❌ No hay archivo .env activo")
    
    # Mostrar resumen de configuración
    try:
        from config import get_config_summary
        summary = get_config_summary()
        print("
📋 Resumen de configuración:")
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for subkey, subvalue in value.items():
                    status = "✅" if subvalue else "❌"
                    print(f"     {status} {subkey}")
            else:
                status = "✅" if value else "❌"
                print(f"   {status} {key}: {value}")
    except ImportError:
        print("⚠️ No se pudo cargar el resumen de configuración")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("🔧 Cambiador de Entorno - ARMind")
        print("="*40)
        print("
Uso:")
        print("  python switch_environment.py <entorno>")
        print("  python switch_environment.py status")
        print("
Entornos disponibles:")
        print("  • development")
        print("  • production")
        print("  • testing")
        print("
Ejemplos:")
        print("  python switch_environment.py development")
        print("  python switch_environment.py status")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_current_environment()
    elif command in ['development', 'production', 'testing']:
        switch_environment(command)
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Usa 'status' o uno de los entornos: development, production, testing")

if __name__ == '__main__':
    main()
