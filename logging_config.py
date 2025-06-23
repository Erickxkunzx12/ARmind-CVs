"""Configuración de Logging Estructurado para ARMind"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import traceback

class StructuredFormatter(logging.Formatter):
    """Formateador de logs estructurados en JSON"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatear log record como JSON estructurado"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Agregar campos extra si están disponibles
        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }
            }
            
            if extra_fields:
                log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class SecurityLogger:
    """Logger especializado para eventos de seguridad"""
    
    def __init__(self, logger_name: str = 'armind.security'):
        self.logger = logging.getLogger(logger_name)
    
    def log_login_attempt(self, username: str, ip_address: str, success: bool, 
                         user_agent: str = None, additional_info: Dict = None):
        """Registrar intento de login"""
        event_data = {
            'event_type': 'login_attempt',
            'username': username,
            'ip_address': ip_address,
            'success': success,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_info:
            event_data.update(additional_info)
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Login attempt: {username} from {ip_address}", 
                       extra=event_data)
    
    def log_permission_denied(self, user_id: int, resource: str, action: str,
                            ip_address: str = None):
        """Registrar acceso denegado"""
        event_data = {
            'event_type': 'permission_denied',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.warning(f"Permission denied: User {user_id} tried to {action} {resource}",
                           extra=event_data)
    
    def log_suspicious_activity(self, description: str, user_id: int = None,
                              ip_address: str = None, severity: str = 'medium',
                              additional_data: Dict = None):
        """Registrar actividad sospechosa"""
        event_data = {
            'event_type': 'suspicious_activity',
            'description': description,
            'user_id': user_id,
            'ip_address': ip_address,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_data:
            event_data.update(additional_data)
        
        level = logging.ERROR if severity == 'high' else logging.WARNING
        self.logger.log(level, f"Suspicious activity: {description}", extra=event_data)
    
    def log_data_access(self, user_id: int, data_type: str, action: str,
                       record_count: int = None, ip_address: str = None):
        """Registrar acceso a datos sensibles"""
        event_data = {
            'event_type': 'data_access',
            'user_id': user_id,
            'data_type': data_type,
            'action': action,
            'record_count': record_count,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Data access: User {user_id} {action} {data_type}",
                        extra=event_data)

class ApplicationLogger:
    """Logger para eventos de la aplicación"""
    
    def __init__(self, logger_name: str = 'armind.app'):
        self.logger = logging.getLogger(logger_name)
    
    def log_cv_analysis(self, user_id: int, cv_filename: str, analysis_duration: float,
                       success: bool, error_message: str = None):
        """Registrar análisis de CV"""
        event_data = {
            'event_type': 'cv_analysis',
            'user_id': user_id,
            'cv_filename': cv_filename,
            'analysis_duration': analysis_duration,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_message:
            event_data['error_message'] = error_message
        
        level = logging.INFO if success else logging.ERROR
        message = f"CV analysis {'completed' if success else 'failed'} for user {user_id}"
        self.logger.log(level, message, extra=event_data)
    
    def log_job_search(self, user_id: int, query: str, location: str,
                      results_count: int, search_duration: float):
        """Registrar búsqueda de empleos"""
        event_data = {
            'event_type': 'job_search',
            'user_id': user_id,
            'query': query,
            'location': location,
            'results_count': results_count,
            'search_duration': search_duration,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Job search: {results_count} results for '{query}' in {location}",
                        extra=event_data)
    
    def log_email_sent(self, recipient: str, email_type: str, success: bool,
                      error_message: str = None):
        """Registrar envío de email"""
        event_data = {
            'event_type': 'email_sent',
            'recipient': recipient,
            'email_type': email_type,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_message:
            event_data['error_message'] = error_message
        
        level = logging.INFO if success else logging.ERROR
        message = f"Email {email_type} {'sent' if success else 'failed'} to {recipient}"
        self.logger.log(level, message, extra=event_data)
    
    def log_api_call(self, api_name: str, endpoint: str, duration: float,
                    success: bool, status_code: int = None, error_message: str = None):
        """Registrar llamada a API externa"""
        event_data = {
            'event_type': 'api_call',
            'api_name': api_name,
            'endpoint': endpoint,
            'duration': duration,
            'success': success,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_message:
            event_data['error_message'] = error_message
        
        level = logging.INFO if success else logging.ERROR
        message = f"API call to {api_name} {'succeeded' if success else 'failed'}"
        self.logger.log(level, message, extra=event_data)

def setup_logging(app_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configurar sistema de logging"""
    
    # Crear directorio de logs si no existe
    log_dir = Path(app_config.get('LOG_DIR', 'logs'))
    log_dir.mkdir(exist_ok=True)
    
    # Configuración base
    log_level = app_config.get('LOG_LEVEL', 'INFO')
    log_format = app_config.get('LOG_FORMAT', 'structured')  # 'structured' o 'simple'
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if log_format == 'structured':
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
    
    root_logger.addHandler(console_handler)
    
    # Handler para archivo general
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'armind.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Handler para errores
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'armind_errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Logger específico para seguridad
    security_logger = logging.getLogger('armind.security')
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10  # Mantener más archivos de seguridad
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(StructuredFormatter())
    security_logger.addHandler(security_handler)
    security_logger.propagate = False  # No propagar al logger raíz
    
    # Logger para acceso HTTP
    access_logger = logging.getLogger('armind.access')
    access_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'access.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(StructuredFormatter())
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # Configurar loggers de terceros
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Crear instancias de loggers especializados
    security_logger_instance = SecurityLogger()
    app_logger_instance = ApplicationLogger()
    
    logging.info("Sistema de logging configurado correctamente")
    
    return {
        'security_logger': security_logger_instance,
        'app_logger': app_logger_instance,
        'log_dir': log_dir
    }

def log_request_middleware(app):
    """Middleware para logging de requests HTTP"""
    
    @app.before_request
    def log_request_start():
        from flask import request, g
        import time
        
        g.start_time = time.time()
        
        # Log básico de request
        access_logger = logging.getLogger('armind.access')
        access_logger.info("Request started", extra={
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'content_length': request.content_length
        })
    
    @app.after_request
    def log_request_end(response):
        from flask import request, g
        import time
        
        duration = time.time() - getattr(g, 'start_time', time.time())
        
        # Log de respuesta
        access_logger = logging.getLogger('armind.access')
        access_logger.info("Request completed", extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': duration,
            'response_size': response.content_length
        })
        
        # Registrar en monitor de aplicación si está disponible
        if hasattr(app, 'app_monitor'):
            app.app_monitor.record_request(
                request.method,
                request.path,
                response.status_code,
                duration
            )
        
        return response
    
    return app