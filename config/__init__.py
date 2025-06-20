#!/usr/bin/env python3
"""
Cargador de Configuración por Entorno - ARMind
"""

import os
from dotenv import load_dotenv

def load_config():
    """Cargar configuración basada en el entorno"""
    
    # Determinar entorno
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    # Cargar archivo .env específico del entorno
    env_file = f'.env.{env}'
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Configuración cargada desde: {env_file}")
    else:
        # Fallback a .env general
        if os.path.exists('.env'):
            load_dotenv('.env')
            print("⚠️ Usando .env general (crear .env específicos por entorno)")
        else:
            print("❌ No se encontró archivo .env")
    
    # Importar configuración específica
    if env == 'production':
        from .production_config import ProductionConfig
        return ProductionConfig
    elif env == 'testing':
        from .testing_config import TestingConfig
        return TestingConfig
    else:  # development (default)
        from .development_config import DevelopmentConfig
        return DevelopmentConfig

def validate_current_config():
    """Validar configuración actual"""
    config_class = load_config()
    validation = config_class.validate_config()
    
    print(f"\n🔧 Validación de configuración ({config_class.FLASK_ENV}):")
    
    if validation['valid']:
        print("✅ Configuración válida")
    else:
        print("❌ Errores en configuración:")
        for error in validation['errors']:
            print(f"   • {error}")
    
    if validation['warnings']:
        print("⚠️ Advertencias:")
        for warning in validation['warnings']:
            print(f"   • {warning}")
    
    return validation

def get_config_summary():
    """Obtener resumen de configuración actual"""
    config_class = load_config()
    return config_class.get_config_summary()

# Exportar función principal
__all__ = ['load_config', 'validate_current_config', 'get_config_summary']
