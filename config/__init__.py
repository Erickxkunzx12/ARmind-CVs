#!/usr/bin/env python3
"""
Cargador de Configuración por Entorno - ARMind
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv('.env')

def load_config():
    """Cargar configuración basada en el entorno"""
    
    # Determinar entorno
    env = os.getenv('FLASK_ENV', 'development').lower()
    
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
