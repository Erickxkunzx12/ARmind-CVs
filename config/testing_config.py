#!/usr/bin/env python3
"""
Configuración de Testing - ARMind
"""

import os
from datetime import timedelta
from .base_config import BaseConfig

class TestingConfig(BaseConfig):
    """Configuración para entorno de testing"""
    
    # Entorno
    DEBUG = False
    TESTING = True
    FLASK_ENV = 'testing'
    
    # Base de datos (testing)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'armind_test')
    DB_USER = os.getenv('DB_USER', 'armind_test_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'test_password')
    
    # Alternativa: SQLite en memoria para tests
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    
    # Seguridad (testing)
    SECRET_KEY = os.getenv('SECRET_KEY', 'test-secret-key-for-automated-tests-only')
    WTF_CSRF_ENABLED = False  # Deshabilitado para tests
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Archivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'test_uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 1024 * 1024))  # 1MB
    
    # APIs externas (mocks)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-test-mock-key')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'sk-ant-test-mock-key')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'test-mock-google-key')
    
    # AWS S3 (mocks)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'test_access_key')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'test_secret_key')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'test-bucket')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', 'test/')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    S3_TESTING_MODE = True
    
    # Email (mocks)
    EMAIL_USER = os.getenv('EMAIL_USER', 'test@test.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'test_password')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
    EMAIL_USE_TLS = False
    EMAIL_TESTING_MODE = True
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')
    LOG_FILE = os.getenv('LOG_FILE', 'test_logs/armind_test.log')
    
    # APIs de trabajo (mocks)
    JOB_API_BASE_URL = os.getenv('JOB_API_BASE_URL', 'http://localhost:8080/mock')
    JOB_API_TIMEOUT = int(os.getenv('JOB_API_TIMEOUT', 5))
    JOB_API_TESTING_MODE = True
    
    # Testing específico
    TEST_DATABASE_CLEANUP = os.getenv('TEST_DATABASE_CLEANUP', 'true').lower() == 'true'
    TEST_FILE_CLEANUP = os.getenv('TEST_FILE_CLEANUP', 'true').lower() == 'true'
    TEST_PARALLEL_EXECUTION = os.getenv('TEST_PARALLEL_EXECUTION', 'false').lower() == 'true'
    
    # Configuración de Flask para tests
    SQLALCHEMY_ECHO = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    @classmethod
    def validate_config(cls):
        """Validar configuración de testing"""
        errors = []
        warnings = []
        
        # Verificar que estamos en modo testing
        if not cls.TESTING:
            errors.append("TESTING debe ser True")
        
        if cls.DEBUG:
            warnings.append("DEBUG está habilitado en testing")
        
        # Verificar base de datos de test
        if cls.DATABASE_URL and 'test' not in cls.DATABASE_URL.lower():
            warnings.append("Base de datos no parece ser de testing")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
