#!/usr/bin/env python3
"""Script de migración gradual para ARMind"""

import os
import sys
from pathlib import Path

def enable_feature(feature_name):
    """Habilitar una característica específica"""
    features = {
        'cache': 'CACHE_ENABLED=true',
        'monitoring': 'MONITORING_ENABLED=true',
        'logging': 'STRUCTURED_LOGGING=true',
        'security': 'ENHANCED_SECURITY=true'
    }
    
    if feature_name not in features:
        print(f"Característica '{feature_name}' no reconocida")
        print(f"Características disponibles: {list(features.keys())}")
        return False
    
    # Leer .env actual
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Actualizar o agregar la configuración
    feature_config = features[feature_name]
    feature_key = feature_config.split('=')[0]
    
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(feature_key):
            lines[i] = feature_config + '
'
            updated = True
            break
    
    if not updated:
        lines.append(feature_config + '
')
    
    # Escribir archivo actualizado
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Característica '{feature_name}' habilitada")
    print("Reinicia la aplicación para aplicar los cambios")
    return True

def disable_feature(feature_name):
    """Deshabilitar una característica específica"""
    features = {
        'cache': 'CACHE_ENABLED=false',
        'monitoring': 'MONITORING_ENABLED=false',
        'logging': 'STRUCTURED_LOGGING=false',
        'security': 'ENHANCED_SECURITY=false'
    }
    
    if feature_name not in features:
        print(f"Característica '{feature_name}' no reconocida")
        return False
    
    # Similar lógica pero con false
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    feature_config = features[feature_name]
    feature_key = feature_config.split('=')[0]
    
    for i, line in enumerate(lines):
        if line.startswith(feature_key):
            lines[i] = feature_config + '
'
            break
    
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Característica '{feature_name}' deshabilitada")
    return True

def show_status():
    """Mostrar estado actual de las características"""
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    features = {
        'Cache': 'CACHE_ENABLED',
        'Monitoreo': 'MONITORING_ENABLED',
        'Logging Estructurado': 'STRUCTURED_LOGGING',
        'Seguridad Mejorada': 'ENHANCED_SECURITY'
    }
    
    print("Estado actual de características:")
    print("-" * 40)
    
    for name, key in features.items():
        if f"{key}=true" in content:
            status = "✅ Habilitado"
        elif f"{key}=false" in content:
            status = "❌ Deshabilitado"
        else:
            status = "❓ No configurado"
        
        print(f"{name:<20}: {status}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python gradual_migration.py <comando> [característica]")
        print("Comandos:")
        print("  enable <feature>   - Habilitar característica")
        print("  disable <feature>  - Deshabilitar característica")
        print("  status            - Mostrar estado actual")
        print("")
        print("Características: cache, monitoring, logging, security")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "enable" and len(sys.argv) > 2:
        enable_feature(sys.argv[2])
    elif command == "disable" and len(sys.argv) > 2:
        disable_feature(sys.argv[2])
    else:
        print("Comando no reconocido")

if __name__ == '__main__':
    main()
