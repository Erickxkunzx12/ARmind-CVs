# Configuración centralizada de la aplicación
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str = 'localhost'
    port: int = 3306
    database: str = 'cv_analyzer'
    user: str = 'root'
    password: str = ''
    charset: str = 'utf8mb4'
    autocommit: bool = True
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            database=os.getenv('DB_NAME', 'cv_analyzer'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            charset=os.getenv('DB_CHARSET', 'utf8mb4'),
            autocommit=os.getenv('DB_AUTOCOMMIT', 'true').lower() == 'true'
        )

@dataclass
class AIConfig:
    """Configuración de proveedores de IA"""
    openai_api_key: str = ''
    anthropic_api_key: str = ''
    gemini_api_key: str = ''
    
    # Modelos por defecto
    openai_model: str = 'gpt-3.5-turbo'
    anthropic_model: str = 'claude-3-5-sonnet-20241022'
    gemini_model: str = 'gemini-pro'
    
    # Configuraciones de API
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'AIConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY', ''),
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            anthropic_model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-pro'),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', '4000')),
            temperature=float(os.getenv('AI_TEMPERATURE', '0.7')),
            timeout=int(os.getenv('AI_TIMEOUT', '30'))
        )

@dataclass
class FileConfig:
    """Configuración de archivos"""
    upload_folder: str = 'uploads'
    max_file_size_mb: int = 10
    allowed_extensions: list = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.pdf', '.docx', '.txt', '.text']
    
    @classmethod
    def from_env(cls) -> 'FileConfig':
        """Crear configuración desde variables de entorno"""
        allowed_ext = os.getenv('ALLOWED_EXTENSIONS', '.pdf,.docx,.txt,.text')
        return cls(
            upload_folder=os.getenv('UPLOAD_FOLDER', 'uploads'),
            max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '10')),
            allowed_extensions=[ext.strip() for ext in allowed_ext.split(',')]
        )

@dataclass
class EmailConfig:
    """Configuración de email"""
    enabled: bool = False
    smtp_server: str = 'smtp.gmail.com'
    smtp_port: int = 587
    username: str = ''
    password: str = ''
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            enabled=os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            username=os.getenv('EMAIL_USERNAME', ''),
            password=os.getenv('EMAIL_PASSWORD', ''),
            use_tls=os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            use_ssl=os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true',
            timeout=int(os.getenv('EMAIL_TIMEOUT', '30')),
            max_retries=int(os.getenv('EMAIL_MAX_RETRIES', '3'))
        )

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    secret_key: str = 'dev-secret-key-change-in-production'
    session_timeout_hours: int = 24
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            secret_key=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            session_timeout_hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '24')),
            password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            password_require_special=os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true',
            password_require_numbers=os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true',
            password_require_uppercase=os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true',
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', '15'))
        )

@dataclass
class AppConfig:
    """Configuración principal de la aplicación"""
    debug: bool = False
    host: str = '127.0.0.1'
    port: int = 5000
    environment: str = 'development'
    log_level: str = 'INFO'
    
    # Configuraciones específicas
    database: DatabaseConfig = None
    ai: AIConfig = None
    files: FileConfig = None
    email: EmailConfig = None
    security: SecurityConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig.from_env()
        if self.ai is None:
            self.ai = AIConfig.from_env()
        if self.files is None:
            self.files = FileConfig.from_env()
        if self.email is None:
            self.email = EmailConfig.from_env()
        if self.security is None:
            self.security = SecurityConfig.from_env()
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Crear configuración desde variables de entorno"""
        return cls(
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            host=os.getenv('HOST', '127.0.0.1'),
            port=int(os.getenv('PORT', '5000')),
            environment=os.getenv('ENVIRONMENT', 'development'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            database=DatabaseConfig.from_env(),
            ai=AIConfig.from_env(),
            files=FileConfig.from_env(),
            email=EmailConfig.from_env(),
            security=SecurityConfig.from_env()
        )
    
    def validate(self) -> Dict[str, Any]:
        """Validar configuración"""
        errors = []
        warnings = []
        
        # Validar claves de API
        if not self.ai.openai_api_key:
            warnings.append('OpenAI API key no configurada')
        
        if not self.ai.anthropic_api_key:
            warnings.append('Anthropic API key no configurada')
        
        if not self.ai.gemini_api_key:
            warnings.append('Gemini API key no configurada')
        
        # Validar configuración de seguridad
        if self.security.secret_key == 'dev-secret-key-change-in-production' and self.environment == 'production':
            errors.append('Secret key debe cambiarse en producción')
        
        # Validar configuración de base de datos
        if not self.database.database:
            errors.append('Nombre de base de datos es requerido')
        
        # Validar configuración de archivos
        if self.files.max_file_size_mb <= 0:
            errors.append('Tamaño máximo de archivo debe ser mayor a 0')
        
        if not self.files.allowed_extensions:
            errors.append('Debe especificar al menos una extensión permitida')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Obtener configuración para Flask"""
        return {
            'SECRET_KEY': self.security.secret_key,
            'DEBUG': self.debug,
            'MAX_CONTENT_LENGTH': self.files.max_file_size_mb * 1024 * 1024,  # Convertir a bytes
            'UPLOAD_FOLDER': self.files.upload_folder,
            'SESSION_PERMANENT': False,
            'PERMANENT_SESSION_LIFETIME': self.security.session_timeout_hours * 3600  # Convertir a segundos
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtener configuración de logging"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                },
                'detailed': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s',
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.log_level,
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': 'app.log',
                    'mode': 'a'
                }
            },
            'loggers': {
                '': {
                    'level': self.log_level,
                    'handlers': ['console', 'file'] if self.environment == 'production' else ['console']
                }
            }
        }

# Configuración global
_config = None

def get_config(config_name: str = None) -> AppConfig:
    """Obtener configuración global"""
    global _config
    if _config is None:
        if config_name:
            _config = get_config_by_environment(config_name)
        else:
            _config = AppConfig.from_env()
    return _config

def set_config(config: AppConfig) -> None:
    """Establecer configuración global"""
    global _config
    _config = config

def load_config_from_file(file_path: str) -> AppConfig:
    """Cargar configuración desde archivo"""
    # Esta función podría implementarse para cargar desde JSON, YAML, etc.
    # Por ahora, solo retornamos la configuración desde variables de entorno
    return AppConfig.from_env()

# Configuraciones predefinidas para diferentes entornos
class DevelopmentConfig(AppConfig):
    """Configuración para desarrollo"""
    def __init__(self):
        super().__init__()
        self.debug = True
        self.environment = 'development'
        self.log_level = 'DEBUG'

class ProductionConfig(AppConfig):
    """Configuración para producción"""
    def __init__(self):
        super().__init__()
        self.debug = False
        self.environment = 'production'
        self.log_level = 'WARNING'
        self.host = '0.0.0.0'

class TestingConfig(AppConfig):
    """Configuración para testing"""
    def __init__(self):
        super().__init__()
        self.debug = True
        self.environment = 'testing'
        self.log_level = 'DEBUG'
        self.database.database = 'cv_analyzer_test'

# Mapeo de configuraciones por entorno
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config_by_environment(env: str) -> AppConfig:
    """Obtener configuración por entorno"""
    config_class = CONFIG_MAP.get(env, AppConfig)
    return config_class()

def validate_config(config: AppConfig) -> bool:
    """Validar configuración de la aplicación"""
    try:
        # Validar configuración de base de datos
        if not config.database.host:
            print("Error: DB_HOST no está configurado")
            return False
        
        if not config.database.database:
            print("Error: DB_NAME no está configurado")
            return False
        
        # Validar al menos una API key de IA
        if not any([
            config.ai.openai_api_key,
            config.ai.anthropic_api_key,
            config.ai.gemini_api_key
        ]):
            print("Advertencia: No hay APIs de IA configuradas")
        
        # Validar configuración de email si está habilitada
        if config.email.enabled:
            if not config.email.smtp_server or not config.email.smtp_port:
                print("Error: Configuración de email incompleta")
                return False
        
        return True
    except Exception as e:
        print(f"Error validando configuración: {e}")
        return False