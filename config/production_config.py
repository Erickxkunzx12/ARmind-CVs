#!/usr/bin/env python3
"""
Configuración de Producción - ARMind
"""

import os
from datetime import timedelta
from .base_config import BaseConfig

class ProductionConfig(BaseConfig):
    """Configuración para entorno de producción"""
    
    # Entorno
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'production'
    
    # Base de datos
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Construir URL de base de datos
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Seguridad (producción)
    SECRET_KEY = os.getenv('SECRET_KEY')
    WTF_CSRF_ENABLED = True
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True  # Solo HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Archivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/var/www/armind/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
    
    # APIs externas
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', 'prod/')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    
    # Email
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/armind/armind.log')
    
    # APIs de trabajo
    JOB_API_BASE_URL = os.getenv('JOB_API_BASE_URL')
    JOB_API_TIMEOUT = int(os.getenv('JOB_API_TIMEOUT', 10))
    
    # Monitoreo
    MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_ENDPOINT = os.getenv('METRICS_ENDPOINT', '/metrics')
    HEALTH_CHECK_ENDPOINT = os.getenv('HEALTH_CHECK_ENDPOINT', '/health')
    
    # Producción específico
    SQLALCHEMY_ECHO = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)
    
    @classmethod
    def validate_config(cls):
        """Validar configuración de producción"""
        errors = []
        warnings = []
        
        # Verificaciones críticas
        required_vars = [
            'SECRET_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'
        ]
        
        for var in required_vars:
            if not getattr(cls, var, None):
                errors.append(f"Variable requerida faltante: {var}")
        
        # Verificar SECRET_KEY segura
        if cls.SECRET_KEY:
            if len(cls.SECRET_KEY) < 32:
                errors.append("SECRET_KEY debe tener al menos 32 caracteres")
            
            if cls.SECRET_KEY.startswith(('dev-', 'test-', 'CHANGE_THIS')):
                errors.append("SECRET_KEY no es segura para producción")
        
        # Verificar configuración HTTPS
        if not cls.SESSION_COOKIE_SECURE:
            errors.append("SESSION_COOKIE_SECURE debe ser True en producción")
        
        # Verificar APIs
        if not any([cls.OPENAI_API_KEY, cls.ANTHROPIC_API_KEY, cls.GOOGLE_API_KEY]):
            warnings.append("No hay claves de API configuradas")
        
        # Verificar AWS
        if cls.S3_BUCKET_NAME and cls.S3_BUCKET_NAME.startswith('tu_'):
            warnings.append("Bucket S3 parece ser de ejemplo")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
