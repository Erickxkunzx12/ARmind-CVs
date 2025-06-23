#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CV Analyzer - Aplicación web para análisis de CVs con IA
Arquitectura modular refactorizada
"""

from flask import Flask
import logging
import logging.config
import os
import sys

# Agregar el directorio src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Imports de la nueva arquitectura
from src.config import get_config, get_config_by_environment
from src.core.database import get_db_service, init_database
from src.services.web_routes import register_web_routes
from src.services.auth_service import get_auth_service
from src.services.file_service import get_file_service
from src.services.cv_analysis_service import get_cv_analysis_service

def create_app(environment: str = None) -> Flask:
    """Factory para crear la aplicación Flask"""
    
    # Determinar entorno
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    # Cargar configuración
    if environment in ['development', 'production', 'testing']:
        config = get_config_by_environment(environment)
    else:
        config = get_config()
    
    # Validar configuración
    validation = config.validate()
    if not validation['is_valid']:
        print("❌ Errores de configuración:")
        for error in validation['errors']:
            print(f"  - {error}")
        sys.exit(1)
    
    if validation['warnings']:
        print("⚠️  Advertencias de configuración:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    # Configurar logging
    logging.config.dictConfig(config.get_logging_config())
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 Iniciando CV Analyzer en modo {environment}")
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Configurar Flask
    app.config.update(config.get_flask_config())
    
    # Crear directorio de uploads si no existe
    upload_folder = config.files.upload_folder
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"📁 Directorio de uploads creado: {upload_folder}")
    
    # Inicializar base de datos
    try:
        logger.info("🔧 Inicializando base de datos...")
        init_database(config.database)
        logger.info("✅ Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        sys.exit(1)
    
    # Verificar servicios
    try:
        logger.info("🔧 Verificando servicios...")
        
        # Verificar servicio de base de datos
        db_service = get_db_service()
        if not db_service.test_connection():
            raise Exception("No se pudo conectar a la base de datos")
        
        # Verificar servicios de aplicación
        auth_service = get_auth_service()
        file_service = get_file_service()
        analysis_service = get_cv_analysis_service()
        
        logger.info("✅ Todos los servicios verificados correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error verificando servicios: {e}")
        sys.exit(1)
    
    # Verificar APIs de IA
    logger.info("🤖 Verificando APIs de IA...")
    
    api_status = {
        'openai': bool(config.ai.openai_api_key),
        'anthropic': bool(config.ai.anthropic_api_key),
        'gemini': bool(config.ai.gemini_api_key)
    }
    
    active_apis = [name for name, status in api_status.items() if status]
    
    if active_apis:
        logger.info(f"✅ APIs de IA configuradas: {', '.join(active_apis)}")
    else:
        logger.warning("⚠️  No hay APIs de IA configuradas")
    
    # Registrar rutas
    logger.info("🛣️  Registrando rutas web...")
    web_routes = register_web_routes(app)
    logger.info("✅ Rutas web registradas correctamente")
    
    # Configurar manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return "Página no encontrada", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno del servidor: {error}")
        return "Error interno del servidor", 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return "Archivo demasiado grande", 413
    
    # Contexto de aplicación
    @app.context_processor
    def inject_config():
        return {
            'app_name': 'CV Analyzer',
            'app_version': '2.0.0',
            'environment': environment,
            'supported_formats': file_service.get_supported_formats(),
            'max_file_size_mb': config.files.max_file_size_mb
        }
    
    # Filtros de template
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('filesize')
    def filesize_filter(value):
        if value is None:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
    
    # Comandos CLI
    @app.cli.command()
    def init_db():
        """Inicializar base de datos"""
        try:
            init_database(config.database)
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    @app.cli.command()
    def test_apis():
        """Probar APIs de IA"""
        from src.core.ai_services import (
            analyze_cv_with_openai,
            analyze_cv_with_anthropic,
            analyze_cv_with_gemini
        )
        
        test_cv = "Nombre: Juan Pérez\nExperiencia: Desarrollador Python con 3 años de experiencia"
        
        # Probar OpenAI
        if config.ai.openai_api_key:
            try:
                result = analyze_cv_with_openai(test_cv, "comprehensive_score")
                print("✅ OpenAI API funcionando")
            except Exception as e:
                print(f"❌ Error en OpenAI API: {e}")
        
        # Probar Anthropic
        if config.ai.anthropic_api_key:
            try:
                result = analyze_cv_with_anthropic(test_cv, "comprehensive_score")
                print("✅ Anthropic API funcionando")
            except Exception as e:
                print(f"❌ Error en Anthropic API: {e}")
        
        # Probar Gemini
        if config.ai.gemini_api_key:
            try:
                result = analyze_cv_with_gemini(test_cv, "comprehensive_score")
                print("✅ Gemini API funcionando")
            except Exception as e:
                print(f"❌ Error en Gemini API: {e}")
    
    @app.cli.command()
    def create_admin():
        """Crear usuario administrador"""
        email = input("Email del administrador: ")
        password = input("Contraseña: ")
        name = input("Nombre (opcional): ") or None
        
        success, result = auth_service.register_user(email, password, name)
        
        if success:
            print(f"✅ Usuario administrador creado: {email}")
        else:
            print(f"❌ Error creando administrador: {result['error']}")
    
    logger.info("🎉 Aplicación inicializada correctamente")
    
    return app

def main():
    """Función principal para ejecutar la aplicación"""
    
    # Obtener configuración
    config = get_config()
    
    # Crear aplicación
    app = create_app()
    
    # Ejecutar aplicación
    print(f"🌐 Servidor iniciando en http://{config.host}:{config.port}")
    print(f"📊 Modo: {config.environment}")
    print(f"🔧 Debug: {config.debug}")
    
    try:
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()