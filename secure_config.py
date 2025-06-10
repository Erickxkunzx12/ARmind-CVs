# Configuración segura para CV Analyzer Pro
# Este archivo debe ser usado para configurar variables de entorno

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class SecureConfig:
    """Configuración segura usando variables de entorno"""
    
    # Clave secreta - DEBE ser cambiada en producción
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-THIS-IN-PRODUCTION-' + os.urandom(24).hex()
    
    # Configuración de la base de datos PostgreSQL
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'cv_analyzer'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', ''),  # DEBE ser configurada
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    # Configuración de OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')  # DEBE ser configurada
    
    # Configuración de Email
    EMAIL_CONFIG = {
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
        'email': os.environ.get('EMAIL_USER', ''),  # DEBE ser configurada
        'password': os.environ.get('EMAIL_PASSWORD', ''),  # DEBE ser configurada
        'use_tls': os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    }
    
    # Configuración de archivos
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuración de desarrollo/producción
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    @staticmethod
    def validate_config():
        """Validar que las configuraciones críticas estén presentes"""
        errors = []
        
        if not SecureConfig.DB_CONFIG['password']:
            errors.append("DB_PASSWORD no está configurada")
            
        if not SecureConfig.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY no está configurada")
            
        if not SecureConfig.EMAIL_CONFIG['email']:
            errors.append("EMAIL_USER no está configurada")
            
        if not SecureConfig.EMAIL_CONFIG['password']:
            errors.append("EMAIL_PASSWORD no está configurada")
            
        return errors

# Función para crear archivo .env de ejemplo
def create_env_example():
    """Crear archivo .env.example con las variables necesarias"""
    env_content = """# Configuración de la base de datos
DB_HOST=localhost
DB_NAME=cv_analyzer
DB_USER=postgres
DB_PASSWORD=tu_password_postgresql
DB_PORT=5432

# Configuración de OpenAI
OPENAI_API_KEY=tu_api_key_de_openai

# Configuración de Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password_gmail
EMAIL_USE_TLS=True

# Configuración de Flask
SECRET_KEY=tu_clave_secreta_muy_segura
FLASK_DEBUG=False
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("Archivo .env.example creado. Cópialo como .env y configura tus valores.")

if __name__ == '__main__':
    create_env_example()