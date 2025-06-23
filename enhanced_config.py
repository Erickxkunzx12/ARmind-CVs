"""Configuración Mejorada para ARMind con Integración de Servicios"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str = 'localhost'
    port: int = 5432
    name: str = 'armind_db'
    user: str = 'postgres'
    password: str = ''
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class RedisConfig:
    """Configuración de Redis"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    
    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

@dataclass
class AIConfig:
    """Configuración de APIs de IA"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    default_model: str = 'gpt-3.5-turbo'
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    
    @property
    def available_providers(self) -> list:
        providers = []
        if self.openai_api_key:
            providers.append('openai')
        if self.anthropic_api_key:
            providers.append('anthropic')
        if self.gemini_api_key:
            providers.append('gemini')
        return providers

@dataclass
class EmailConfig:
    """Configuración de email"""
    smtp_server: str = 'smtp.gmail.com'
    smtp_port: int = 587
    username: str = ''
    password: str = ''
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    max_retries: int = 3
    
    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password)

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    secret_key: str = ''
    jwt_secret_key: str = ''
    jwt_access_token_expires: int = 3600  # 1 hora
    jwt_refresh_token_expires: int = 2592000  # 30 días
    password_min_length: int = 8
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutos
    session_timeout: int = 3600  # 1 hora
    csrf_enabled: bool = True
    
    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key and self.jwt_secret_key)

@dataclass
class FileConfig:
    """Configuración de archivos"""
    upload_folder: str = 'uploads'
    max_file_size: int = 16 * 1024 * 1024  # 16MB
    allowed_extensions: set = field(default_factory=lambda: {'pdf', 'doc', 'docx', 'txt'})
    temp_folder: str = 'temp'
    
    def __post_init__(self):
        # Crear directorios si no existen
        Path(self.upload_folder).mkdir(exist_ok=True)
        Path(self.temp_folder).mkdir(exist_ok=True)

@dataclass
class MonitoringConfig:
    """Configuración de monitoreo"""
    enabled: bool = True
    metrics_interval: int = 30  # segundos
    health_check_interval: int = 60  # segundos
    log_level: str = 'INFO'
    log_format: str = 'structured'  # 'structured' o 'simple'
    log_dir: str = 'logs'
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    def __post_init__(self):
        # Crear directorio de logs si no existe
        Path(self.log_dir).mkdir(exist_ok=True)

@dataclass
class CacheConfig:
    """Configuración de cache"""
    enabled: bool = True
    default_ttl: int = 3600  # 1 hora
    cv_analysis_ttl: int = 3600  # 1 hora
    job_search_ttl: int = 1800  # 30 minutos
    user_session_ttl: int = 86400  # 24 horas
    max_memory_usage: str = '256mb'

@dataclass
class PerformanceConfig:
    """Configuración de rendimiento"""
    enable_gzip: bool = True
    enable_etag: bool = True
    static_cache_timeout: int = 31536000  # 1 año
    api_rate_limit: str = '100/hour'
    max_workers: int = 4
    worker_timeout: int = 30
    keep_alive: int = 2

class EnhancedConfig:
    """Configuración mejorada de ARMind"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('FLASK_ENV', 'development')
        self.debug = self.environment == 'development'
        
        # Cargar configuraciones
        self.database = self._load_database_config()
        self.redis = self._load_redis_config()
        self.ai = self._load_ai_config()
        self.email = self._load_email_config()
        self.security = self._load_security_config()
        self.files = self._load_file_config()
        self.monitoring = self._load_monitoring_config()
        self.cache = self._load_cache_config()
        self.performance = self._load_performance_config()
        
        # Configuraciones Flask
        self.flask_config = self._build_flask_config()
        
        # Validar configuración
        self._validate_config()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Cargar configuración de base de datos"""
        return DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            name=os.getenv('DB_NAME', 'armind_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20'))
        )
    
    def _load_redis_config(self) -> RedisConfig:
        """Cargar configuración de Redis"""
        return RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
        )
    
    def _load_ai_config(self) -> AIConfig:
        """Cargar configuración de IA"""
        return AIConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            default_model=os.getenv('AI_DEFAULT_MODEL', 'gpt-3.5-turbo'),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', '2000')),
            temperature=float(os.getenv('AI_TEMPERATURE', '0.7'))
        )
    
    def _load_email_config(self) -> EmailConfig:
        """Cargar configuración de email"""
        return EmailConfig(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            username=os.getenv('SMTP_USERNAME', ''),
            password=os.getenv('SMTP_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Cargar configuración de seguridad"""
        return SecurityConfig(
            secret_key=os.getenv('SECRET_KEY', ''),
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', ''),
            jwt_access_token_expires=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration=int(os.getenv('LOCKOUT_DURATION', '900'))
        )
    
    def _load_file_config(self) -> FileConfig:
        """Cargar configuración de archivos"""
        return FileConfig(
            upload_folder=os.getenv('UPLOAD_FOLDER', 'uploads'),
            max_file_size=int(os.getenv('MAX_FILE_SIZE', str(16 * 1024 * 1024))),
            temp_folder=os.getenv('TEMP_FOLDER', 'temp')
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Cargar configuración de monitoreo"""
        return MonitoringConfig(
            enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            metrics_interval=int(os.getenv('METRICS_INTERVAL', '30')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_format=os.getenv('LOG_FORMAT', 'structured'),
            log_dir=os.getenv('LOG_DIR', 'logs')
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """Cargar configuración de cache"""
        return CacheConfig(
            enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', '3600')),
            cv_analysis_ttl=int(os.getenv('CACHE_CV_ANALYSIS_TTL', '3600')),
            job_search_ttl=int(os.getenv('CACHE_JOB_SEARCH_TTL', '1800'))
        )
    
    def _load_performance_config(self) -> PerformanceConfig:
        """Cargar configuración de rendimiento"""
        return PerformanceConfig(
            enable_gzip=os.getenv('ENABLE_GZIP', 'true').lower() == 'true',
            enable_etag=os.getenv('ENABLE_ETAG', 'true').lower() == 'true',
            api_rate_limit=os.getenv('API_RATE_LIMIT', '100/hour'),
            max_workers=int(os.getenv('MAX_WORKERS', '4'))
        )
    
    def _build_flask_config(self) -> Dict[str, Any]:
        """Construir configuración de Flask"""
        config = {
            'DEBUG': self.debug,
            'TESTING': False,
            'SECRET_KEY': self.security.secret_key,
            'SQLALCHEMY_DATABASE_URI': self.database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.database.pool_size,
                'max_overflow': self.database.max_overflow,
                'pool_timeout': self.database.pool_timeout,
                'pool_recycle': self.database.pool_recycle
            },
            'REDIS_URL': self.redis.url,
            'MAX_CONTENT_LENGTH': self.files.max_file_size,
            'UPLOAD_FOLDER': self.files.upload_folder,
            'SEND_FILE_MAX_AGE_DEFAULT': self.performance.static_cache_timeout,
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': self.debug
        }
        
        # Configuraciones específicas del entorno
        if self.environment == 'production':
            config.update({
                'SESSION_COOKIE_SECURE': True,
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax',
                'PERMANENT_SESSION_LIFETIME': self.security.session_timeout
            })
        
        return config
    
    def _validate_config(self):
        """Validar configuración"""
        errors = []
        
        # Validar configuración de seguridad
        if not self.security.is_configured:
            errors.append("SECRET_KEY y JWT_SECRET_KEY son requeridos")
        
        # Validar configuración de base de datos
        if not self.database.password and self.environment == 'production':
            errors.append("DB_PASSWORD es requerido en producción")
        
        # Validar configuración de IA
        if not self.ai.available_providers:
            errors.append("Al menos una API key de IA debe estar configurada")
        
        if errors:
            error_msg = "Errores de configuración:\n" + "\n".join(f"- {error}" for error in errors)
            if self.environment == 'production':
                raise ValueError(error_msg)
            else:
                logging.warning(error_msg)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de configuración"""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'name': self.database.name,
                'pool_size': self.database.pool_size
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'db': self.redis.db
            },
            'ai': {
                'available_providers': self.ai.available_providers,
                'default_model': self.ai.default_model
            },
            'email': {
                'configured': self.email.is_configured,
                'server': self.email.smtp_server
            },
            'security': {
                'configured': self.security.is_configured,
                'max_login_attempts': self.security.max_login_attempts
            },
            'monitoring': {
                'enabled': self.monitoring.enabled,
                'log_level': self.monitoring.log_level
            },
            'cache': {
                'enabled': self.cache.enabled,
                'default_ttl': self.cache.default_ttl
            }
        }

# Instancia global de configuración
config = None

def init_config(environment: str = None) -> EnhancedConfig:
    """Inicializar configuración global"""
    global config
    config = EnhancedConfig(environment)
    return config

def get_config() -> EnhancedConfig:
    """Obtener configuración global"""
    global config
    if config is None:
        config = init_config()
    return config