#!/usr/bin/env python3
"""
Configuración de Desarrollo - ARMind
"""

import os
from datetime import timedelta
from .base_config import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Configuración para entorno de desarrollo"""
    
    # Entorno
    DEBUG = True
    TESTING = False
    FLASK_ENV = 'development'
    
    # Base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'armind_dev')
    DB_USER = os.getenv('DB_USER', 'armind_dev_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'dev_password_123')
    
    # Construir URL de base de datos
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Seguridad (desarrollo)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_ENABLED = False  # Deshabilitado para desarrollo
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = False  # HTTP permitido en desarrollo
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Archivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads_dev')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # APIs externas
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'armind-dev-bucket')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', 'dev/')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    
    # Email
    EMAIL_USER = os.getenv('EMAIL_USER', 'test@example.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'test_password')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'false').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/armind_dev.log')
    
    # APIs de trabajo
    JOB_API_BASE_URL = os.getenv('JOB_API_BASE_URL', 'https://api-dev.example.com')
    JOB_API_TIMEOUT = int(os.getenv('JOB_API_TIMEOUT', 30))
    
    # Desarrollo específico
    SQLALCHEMY_ECHO = True  # Mostrar queries SQL
    SEND_FILE_MAX_AGE_DEFAULT = 0  # No cache para desarrollo
    
    @classmethod
    def validate_config(cls):
        """Validar configuración de desarrollo"""
        errors = []
        warnings = []
        
        # Verificar base de datos
        if not all([cls.DB_HOST, cls.DB_NAME, cls.DB_USER, cls.DB_PASSWORD]):
            errors.append("Configuración de base de datos incompleta")
        
        # Advertencias para desarrollo
        if cls.SECRET_KEY.startswith('dev-'):
            warnings.append("Usando SECRET_KEY de desarrollo")
        
        if not cls.SESSION_COOKIE_SECURE:
            warnings.append("Cookies de sesión no seguras (normal en desarrollo)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
