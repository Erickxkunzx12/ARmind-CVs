"""Capa de compatibilidad para ARMind"""

import os
import sys
from functools import wraps

def safe_import(module_name, fallback=None):
    """Importar módulo de forma segura con fallback"""
    try:
        return __import__(module_name)
    except ImportError:
        if fallback:
            return fallback
        return None

def feature_flag(feature_name, default=False):
    """Decorator para características opcionales"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            enabled = os.environ.get(f"{feature_name.upper()}_ENABLED", str(default)).lower() == 'true'
            if enabled:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error en característica {feature_name}: {e}")
                    return None
            return None
        return wrapper
    return decorator

def graceful_fallback(fallback_func):
    """Decorator para fallback graceful"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Fallback activado para {func.__name__}: {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator

class CompatibilityManager:
    """Gestor de compatibilidad"""
    
    def __init__(self):
        self.features = {}
        self.fallbacks = {}
    
    def register_feature(self, name, implementation, fallback=None):
        """Registrar una característica con fallback"""
        self.features[name] = implementation
        if fallback:
            self.fallbacks[name] = fallback
    
    def get_feature(self, name):
        """Obtener implementación de característica"""
        if name in self.features:
            enabled = os.environ.get(f"{name.upper()}_ENABLED", 'false').lower() == 'true'
            if enabled:
                return self.features[name]
        
        return self.fallbacks.get(name, lambda *args, **kwargs: None)

# Instancia global
compat_manager = CompatibilityManager()
