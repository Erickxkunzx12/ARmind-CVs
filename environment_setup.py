#!/usr/bin/env python3
"""
Configurador de Entornos para ARMind
Crea configuraciones separadas para desarrollo, producción y testing.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List

class EnvironmentSetup:
    """Configurador de entornos de desarrollo"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.environments = ['development', 'production', 'testing']
    
    def create_environment_configs(self):
        """Crear archivos de configuración por entorno"""
        print("🔧 Creando configuraciones por entorno...")
        
        # Crear directorio de configuraciones
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        for env in self.environments:
            self._create_env_file(env)
            self._create_env_config_file(env)
        
        # Crear archivo de configuración base
        self._create_base_config()
        
        print("✅ Configuraciones de entorno creadas")
    
    def _create_env_file(self, environment: str):
        """Crear archivo .env para entorno específico"""
        env_file = self.project_root / f'.env.{environment}'
        
        if environment == 'development':
            content = self._get_development_env()
        elif environment == 'production':
            content = self._get_production_env()
        else:  # testing
            content = self._get_testing_env()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Creado: {env_file.name}")
    
    def _create_env_config_file(self, environment: str):
        """Crear archivo de configuración Python por entorno"""
        config_dir = self.project_root / 'config'
        config_file = config_dir / f'{environment}_config.py'
        
        if environment == 'development':
            content = self._get_development_config()
        elif environment == 'production':
            content = self._get_production_config()
        else:  # testing
            content = self._get_testing_config()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Creado: config/{config_file.name}")
    
    def _get_development_env(self) -> str:
        """Configuración .env para desarrollo"""
        return """
# =============================================================================
# CONFIGURACIÓN DE DESARROLLO - ARMind
# =============================================================================
# ⚠️ SOLO para desarrollo local - NO usar en producción

# Entorno
FLASK_ENV=development
DEBUG=true

# Seguridad (desarrollo)
SECRET_KEY=dev-secret-key-change-in-production-12345678901234567890

# Base de Datos (desarrollo local)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=armind_dev
DB_USER=armind_dev_user
DB_PASSWORD=dev_password_123

# APIs (desarrollo - usar claves de prueba)
# OPENAI_API_KEY=sk-test-your-development-key-here
# ANTHROPIC_API_KEY=sk-ant-test-your-development-key-here
# GOOGLE_API_KEY=test-your-google-development-key-here

# Email (desarrollo - usar servicio de prueba)
EMAIL_USER=test@example.com
EMAIL_PASSWORD=test_password
SMTP_SERVER=localhost
SMTP_PORT=1025
EMAIL_USE_TLS=false

# AWS S3 (desarrollo - usar bucket de prueba)
# Preferir IAM roles, pero si necesitas credenciales:
# AWS_ACCESS_KEY_ID=tu_access_key_desarrollo
# AWS_SECRET_ACCESS_KEY=tu_secret_key_desarrollo
S3_BUCKET_NAME=armind-dev-bucket
S3_FOLDER_PREFIX=dev/
S3_REGION=us-east-1

# Configuración de archivos
UPLOAD_FOLDER=uploads_dev
MAX_CONTENT_LENGTH=16777216

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/armind_dev.log

# URLs de APIs externas (desarrollo)
JOB_API_BASE_URL=https://api-dev.example.com
JOB_API_TIMEOUT=30

# Configuración de sesión
SESSION_LIFETIME=3600
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
"""
    
    def _get_production_env(self) -> str:
        """Configuración .env para producción"""
        return """
# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN - ARMind
# =============================================================================
# 🔒 PRODUCCIÓN - Todas las credenciales deben ser seguras

# Entorno
FLASK_ENV=production
DEBUG=false

# Seguridad (REQUERIDO - generar clave segura)
SECRET_KEY=CHANGE_THIS_TO_SECURE_RANDOM_KEY_32_CHARS_MINIMUM

# Base de Datos (producción)
DB_HOST=your-production-db-host.com
DB_PORT=5432
DB_NAME=armind_prod
DB_USER=armind_prod_user
DB_PASSWORD=SECURE_PRODUCTION_PASSWORD

# APIs (producción - claves reales)
OPENAI_API_KEY=sk-your-production-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-production-anthropic-key-here
GOOGLE_API_KEY=your-production-google-key-here

# Email (producción)
EMAIL_USER=noreply@yourdomain.com
EMAIL_PASSWORD=SECURE_EMAIL_PASSWORD
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
EMAIL_USE_TLS=true

# AWS S3 (producción - preferir IAM roles)
# ⚠️ Usar IAM roles en lugar de credenciales cuando sea posible
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=armind-production-bucket
S3_FOLDER_PREFIX=prod/
S3_REGION=us-east-1

# Configuración de archivos
UPLOAD_FOLDER=/var/www/armind/uploads
MAX_CONTENT_LENGTH=52428800

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/armind/armind.log

# URLs de APIs externas (producción)
JOB_API_BASE_URL=https://api.production-service.com
JOB_API_TIMEOUT=10

# Configuración de sesión
SESSION_LIFETIME=1800
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict

# Monitoreo y métricas
MONITORING_ENABLED=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_ENDPOINT=/health
"""
    
    def _get_testing_env(self) -> str:
        """Configuración .env para testing"""
        return """
# =============================================================================
# CONFIGURACIÓN DE TESTING - ARMind
# =============================================================================
# 🧪 TESTING - Configuración para pruebas automatizadas

# Entorno
FLASK_ENV=testing
DEBUG=false
TESTING=true

# Seguridad (testing)
SECRET_KEY=test-secret-key-for-automated-tests-only

# Base de Datos (testing - en memoria o temporal)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=armind_test
DB_USER=armind_test_user
DB_PASSWORD=test_password
# Alternativa: usar SQLite en memoria
# DATABASE_URL=sqlite:///:memory:

# APIs (testing - usar mocks o claves de prueba)
# OPENAI_API_KEY=sk-test-mock-key-for-testing
# ANTHROPIC_API_KEY=sk-ant-test-mock-key-for-testing
# GOOGLE_API_KEY=test-mock-google-key

# Email (testing - usar mock)
EMAIL_USER=test@test.com
EMAIL_PASSWORD=test_password
SMTP_SERVER=localhost
SMTP_PORT=1025
EMAIL_USE_TLS=false
EMAIL_TESTING_MODE=true

# AWS S3 (testing - usar mocks)
# AWS_ACCESS_KEY_ID=test_access_key
# AWS_SECRET_ACCESS_KEY=test_secret_key
S3_BUCKET_NAME=test-bucket
S3_FOLDER_PREFIX=test/
S3_REGION=us-east-1
S3_TESTING_MODE=true

# Configuración de archivos
UPLOAD_FOLDER=test_uploads
MAX_CONTENT_LENGTH=1048576

# Logging
LOG_LEVEL=WARNING
LOG_FILE=test_logs/armind_test.log

# URLs de APIs externas (testing - mocks)
JOB_API_BASE_URL=http://localhost:8080/mock
JOB_API_TIMEOUT=5
JOB_API_TESTING_MODE=true

# Configuración de sesión
SESSION_LIFETIME=300
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true

# Testing específico
TEST_DATABASE_CLEANUP=true
TEST_FILE_CLEANUP=true
TEST_PARALLEL_EXECUTION=false
"""
    
    def _get_development_config(self) -> str:
        """Configuración Python para desarrollo"""
        return '''#!/usr/bin/env python3
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
'''
    
    def _get_production_config(self) -> str:
        """Configuración Python para producción"""
        return '''#!/usr/bin/env python3
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
'''
    
    def _get_testing_config(self) -> str:
        """Configuración Python para testing"""
        return '''#!/usr/bin/env python3
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
'''
    
    def _create_base_config(self):
        """Crear configuración base"""
        config_dir = self.project_root / 'config'
        base_config_file = config_dir / 'base_config.py'
        
        content = '''#!/usr/bin/env python3
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
'''
        
        with open(base_config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Creado: config/base_config.py")
    
    def create_environment_loader(self):
        """Crear cargador de configuración por entorno"""
        config_dir = self.project_root / 'config'
        loader_file = config_dir / '__init__.py'
        
        content = '''#!/usr/bin/env python3
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
'''
        
        with open(loader_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Creado: config/__init__.py")
    
    def create_environment_switcher_script(self):
        """Crear script para cambiar entre entornos"""
        script_file = self.project_root / 'switch_environment.py'
        
        content = '''#!/usr/bin/env python3
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
        print("\n📋 Resumen de configuración:")
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
        print("\nUso:")
        print("  python switch_environment.py <entorno>")
        print("  python switch_environment.py status")
        print("\nEntornos disponibles:")
        print("  • development")
        print("  • production")
        print("  • testing")
        print("\nEjemplos:")
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
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Creado: switch_environment.py")
    
    def create_gitignore_update(self):
        """Actualizar .gitignore para entornos"""
        gitignore_file = self.project_root / '.gitignore'
        
        gitignore_additions = """
# Archivos de configuración por entorno
.env
.env.local
.env.*.local
.env.backup

# Logs por entorno
logs/
test_logs/
*.log

# Uploads por entorno
uploads_dev/
test_uploads/

# Configuración de seguridad
security.log
security_audit.json
credentials_metadata.json
aws_iam_config.json

# Archivos temporales de testing
.pytest_cache/
.coverage
htmlcov/
"""
        
        # Leer .gitignore existente
        existing_content = ""
        if gitignore_file.exists():
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Agregar nuevas entradas si no existen
        if "# Archivos de configuración por entorno" not in existing_content:
            with open(gitignore_file, 'a', encoding='utf-8') as f:
                f.write(gitignore_additions)
            print("📄 Actualizado: .gitignore")
        else:
            print("ℹ️ .gitignore ya contiene configuraciones de entorno")
    
    def setup_complete_environment_structure(self):
        """Configurar estructura completa de entornos"""
        print("🚀 Configurando estructura completa de entornos...")
        print("="*60)
        
        # Crear todas las configuraciones
        self.create_environment_configs()
        self.create_environment_loader()
        self.create_environment_switcher_script()
        self.create_gitignore_update()
        
        # Crear directorios necesarios
        directories = ['logs', 'test_logs', 'uploads_dev', 'test_uploads']
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            print(f"📁 Creado directorio: {directory}")
        
        print("\n✅ Estructura de entornos configurada exitosamente")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Revisar y personalizar archivos .env.* según tu entorno")
        print("2. Configurar credenciales reales en .env.production")
        print("3. Usar 'python switch_environment.py development' para cambiar entornos")
        print("4. Ejecutar 'python switch_environment.py status' para verificar configuración")
        print("\n⚠️ IMPORTANTE:")
        print("• NO commitear archivos .env con credenciales reales")
        print("• Usar .env.example como plantilla para el equipo")
        print("• Configurar variables de entorno en producción")

def main():
    """Función principal"""
    print("🔧 Configurador de Entornos - ARMind")
    print("="*50)
    
    setup = EnvironmentSetup()
    setup.setup_complete_environment_structure()

if __name__ == '__main__':
    main()