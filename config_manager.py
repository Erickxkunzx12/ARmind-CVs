#!/usr/bin/env python3
"""
Gestor de Configuración Centralizado para ARMind
Maneja configuraciones para diferentes entornos (desarrollo, producción, testing)
con validación de variables de entorno y logging de seguridad.
"""

import os
import logging
from datetime import timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import secrets

# Configurar logging de seguridad
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_logger = logging.getLogger('security')

class ConfigurationError(Exception):
    """Excepción personalizada para errores de configuración"""
    pass

class BaseConfig:
    """Configuración base con validaciones de seguridad"""
    
    def __init__(self):
        # Cargar variables de entorno desde .env
        load_dotenv()
        
        # Validar configuración al inicializar
        self._validate_required_vars()
        
        # Log de inicialización segura
        security_logger.info(f"Configuración inicializada para entorno: {self.ENVIRONMENT}")
    
    # Variables de entorno requeridas
    REQUIRED_VARS = [
        'SECRET_KEY',
        'DB_HOST',
        'DB_NAME', 
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    # Configuración básica
    ENVIRONMENT = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Clave secreta - generada automáticamente si no existe
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(32)
    
    # Configuración de base de datos PostgreSQL
    @property
    def DATABASE_CONFIG(self) -> Dict[str, str]:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'cv_analyzer'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    # Configuración de APIs de IA
    @property
    def AI_APIS_CONFIG(self) -> Dict[str, Optional[str]]:
        return {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY')
        }
    
    # Configuración de AWS (usando IAM roles cuando sea posible)
    @property
    def AWS_CONFIG(self) -> Dict[str, str]:
        return {
            'access_key_id': os.getenv('AWS_ACCESS_KEY_ID', ''),
            'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'bucket_name': os.getenv('S3_BUCKET_NAME', ''),
            'folder_prefix': os.getenv('S3_FOLDER_PREFIX', 'cv-analysis/')
        }
    
    # Configuración de email
    @property
    def EMAIL_CONFIG(self) -> Dict[str, Any]:
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('EMAIL_USER', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
        }
    
    # Configuración de archivos
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    def _validate_required_vars(self):
        """Validar que todas las variables requeridas estén configuradas"""
        missing_vars = []
        
        for var in self.REQUIRED_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"Variables de entorno faltantes: {', '.join(missing_vars)}"
            security_logger.error(error_msg)
            raise ConfigurationError(error_msg)
    
    def validate_ai_apis(self) -> Dict[str, bool]:
        """Validar disponibilidad de APIs de IA"""
        apis_status = {}
        for api_name, api_key in self.AI_APIS_CONFIG.items():
            apis_status[api_name] = bool(api_key and not api_key.startswith('tu_'))
            
        security_logger.info(f"Estado de APIs de IA: {apis_status}")
        return apis_status
    
    def validate_aws_config(self) -> bool:
        """Validar configuración de AWS"""
        aws_config = self.AWS_CONFIG
        
        # Verificar si se están usando IAM roles (preferido)
        if not aws_config['access_key_id'] and not aws_config['secret_access_key']:
            security_logger.info("Usando IAM roles para AWS (recomendado)")
            return True
        
        # Verificar credenciales explícitas
        if aws_config['access_key_id'] and aws_config['secret_access_key']:
            # Verificar que no sean valores de ejemplo
            if (aws_config['access_key_id'].startswith('tu_') or 
                aws_config['secret_access_key'].startswith('tu_')):
                security_logger.warning("Credenciales AWS contienen valores de ejemplo")
                return False
            
            security_logger.info("Credenciales AWS configuradas")
            return True
        
        security_logger.warning("Configuración AWS incompleta")
        return False
    
    def validate_email_config(self) -> bool:
        """Validar configuración de email"""
        email_config = self.EMAIL_CONFIG
        
        if not email_config['email'] or not email_config['password']:
            security_logger.warning("Configuración de email incompleta")
            return False
        
        # Verificar valores de ejemplo
        example_values = ['tu_email@gmail.com', 'tu_email@outlook.com', 'tu_app_password']
        if (email_config['email'] in example_values or 
            email_config['password'] in example_values):
            security_logger.warning("Configuración de email contiene valores de ejemplo")
            return False
        
        security_logger.info(f"Email configurado: {email_config['email']}")
        return True

class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    ENVIRONMENT = 'development'
    
    # En desarrollo, las APIs opcionales no son críticas
    REQUIRED_VARS = [
        'SECRET_KEY',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]

class ProductionConfig(BaseConfig):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    ENVIRONMENT = 'production'
    
    # En producción, requerir más configuraciones
    REQUIRED_VARS = [
        'SECRET_KEY',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'OPENAI_API_KEY'  # Al menos una API de IA requerida
    ]
    
    def __init__(self):
        super().__init__()
        
        # Validaciones adicionales para producción
        if self.SECRET_KEY.startswith('dev-') or len(self.SECRET_KEY) < 32:
            raise ConfigurationError("SECRET_KEY insegura para producción")
        
        # Log de seguridad para producción
        security_logger.info("Configuración de producción inicializada")
        security_logger.info(f"Base de datos: {self.DATABASE_CONFIG['host']}")

class TestingConfig(BaseConfig):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    ENVIRONMENT = 'testing'
    
    # Base de datos de prueba
    @property
    def DATABASE_CONFIG(self) -> Dict[str, str]:
        return {
            'host': os.getenv('TEST_DB_HOST', 'localhost'),
            'database': os.getenv('TEST_DB_NAME', 'cv_analyzer_test'),
            'user': os.getenv('TEST_DB_USER', 'postgres'),
            'password': os.getenv('TEST_DB_PASSWORD', ''),
            'port': os.getenv('TEST_DB_PORT', '5432')
        }

# Mapeo de configuraciones
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(environment: str = None) -> BaseConfig:
    """Obtener configuración para el entorno especificado"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_map.get(environment, config_map['default'])
    return config_class()

class ConfigManager:
    """Gestor centralizado de configuración"""
    
    def __init__(self, environment: str = None):
        self.config = get_config(environment)
    
    def get_database_config(self) -> Dict[str, str]:
        """Obtener configuración de base de datos"""
        return self.config.DATABASE_CONFIG
    
    def get_ai_apis_config(self) -> Dict[str, Optional[str]]:
        """Obtener configuración de APIs de IA"""
        return self.config.AI_APIS_CONFIG
    
    def get_aws_config(self) -> Dict[str, str]:
        """Obtener configuración de AWS"""
        return self.config.AWS_CONFIG
    
    def get_email_config(self) -> Dict[str, Any]:
        """Obtener configuración de email"""
        return self.config.EMAIL_CONFIG
    
    def validate_email_config(self) -> bool:
        """Validar configuración de email"""
        return self.config.validate_email_config()
    
    def validate_ai_apis(self) -> Dict[str, bool]:
        """Validar APIs de IA"""
        return self.config.validate_ai_apis()
    
    def validate_aws_config(self) -> bool:
        """Validar configuración de AWS"""
        return self.config.validate_aws_config()
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Obtener configuración de Flask"""
        return {
            'SECRET_KEY': self.config.SECRET_KEY,
            'UPLOAD_FOLDER': self.config.UPLOAD_FOLDER,
            'MAX_CONTENT_LENGTH': self.config.MAX_CONTENT_LENGTH,
            'DEBUG': self.config.DEBUG,
            'TESTING': self.config.TESTING
        }
    
    def get_api_config(self) -> Dict[str, Optional[str]]:
        """Obtener configuración de APIs (alias para get_ai_apis_config)"""
        ai_config = self.get_ai_apis_config()
        return {
            'OPENAI_API_KEY': ai_config['openai'],
            'ANTHROPIC_API_KEY': ai_config['anthropic'],
            'GEMINI_API_KEY': ai_config['gemini']
        }

# Función de conveniencia para validar toda la configuración
def validate_full_config(config: BaseConfig) -> Dict[str, bool]:
    """Validar toda la configuración y retornar estado"""
    validation_results = {
        'ai_apis': config.validate_ai_apis(),
        'aws_config': config.validate_aws_config(),
        'email_config': config.validate_email_config()
    }
    
    security_logger.info(f"Validación completa: {validation_results}")
    return validation_results