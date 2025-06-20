#!/usr/bin/env python3
"""
Configuración Base - ARMind
"""

import os
from abc import ABC, abstractmethod

class BaseConfig(ABC):
    """Configuración base para todos los entornos"""
    
    # Configuración común
    PROJECT_NAME = 'ARMind CV Analyzer'
    VERSION = '1.0.0'
    
    # Flask
    FLASK_APP = 'app.py'
    
    # Internacionalización
    LANGUAGES = ['es', 'en']
    DEFAULT_LANGUAGE = 'es'
    
    # Formatos de archivo permitidos
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    
    # Configuración de APIs
    API_RATE_LIMIT = '100 per hour'
    API_TIMEOUT = 30
    
    # Configuración de seguridad común
    BCRYPT_LOG_ROUNDS = 12
    PASSWORD_MIN_LENGTH = 8
    
    @classmethod
    @abstractmethod
    def validate_config(cls):
        """Validar configuración específica del entorno"""
        pass
    
    @classmethod
    def get_config_summary(cls):
        """Obtener resumen de configuración"""
        return {
            'environment': cls.FLASK_ENV,
            'debug': cls.DEBUG,
            'testing': cls.TESTING,
            'database_configured': bool(getattr(cls, 'DATABASE_URL', None)),
            'apis_configured': {
                'openai': bool(getattr(cls, 'OPENAI_API_KEY', None)),
                'anthropic': bool(getattr(cls, 'ANTHROPIC_API_KEY', None)),
                'google': bool(getattr(cls, 'GOOGLE_API_KEY', None))
            },
            'aws_configured': bool(getattr(cls, 'S3_BUCKET_NAME', None)),
            'email_configured': bool(getattr(cls, 'EMAIL_USER', None))
        }
