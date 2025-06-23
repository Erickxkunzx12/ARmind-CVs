import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de la base de datos MySQL
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST') or 'localhost',
        'user': os.environ.get('DB_USER') or 'root',
        'password': os.environ.get('DB_PASSWORD') or '',
        'database': os.environ.get('DB_NAME') or 'cv_analyzer_db',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    # Configuración de OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-openai-api-key-here'
    
    # Configuración de Anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or 'your-anthropic-api-key-here'
    
    # Configuración de Google Gemini
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'your-gemini-api-key-here'
    
    # Configuración de AWS S3
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or 'your-aws-access-key-here'
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or 'your-aws-secret-key-here'
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME') or 'armind-cv-analysis'
    S3_FOLDER_PREFIX = os.environ.get('S3_FOLDER_PREFIX') or 'cv-analysis/'
    
    # Configuración de archivos
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuración de APIs de empleo
    JOB_APIS = {
        'computrabajo': {
            'base_url': 'https://www.computrabajo.com',
            'search_endpoint': '/empleos-publicados-en-{location}?q={query}'
        },
        'indeed': {
            'base_url': 'https://www.indeed.com',
            'search_endpoint': '/jobs?q={query}&l={location}'
        }
    }
    
class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    
# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}