#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación principal con nueva arquitectura modular
ARMind - Analizador de CV con IA
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar src al path para imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from flask import Flask
from config import get_config, validate_config
from core.database import get_db_service
from services.auth_service import get_auth_service
from services.file_service import get_file_service
from services.cv_analysis_service import get_cv_analysis_service
from services.web_routes import WebRoutes
import logging
from datetime import datetime

def create_app(config_name=None):
    """
    Factory function para crear la aplicación Flask
    
    Args:
        config_name: Nombre del entorno (development, production, testing)
    
    Returns:
        Flask: Instancia de la aplicación configurada
    """
    app = Flask(__name__)
    
    try:
        # 1. Cargar y validar configuración
        config = get_config(config_name)
        if not validate_config(config):
            raise ValueError("Configuración inválida")
        
        # 2. Configurar Flask
        app.config.update(config.get_flask_config())
        
        # 3. Configurar logging
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Iniciando aplicación en modo {config.environment}")
        
        # 4. Inicializar base de datos
        db_service = get_db_service()
        if not db_service.test_connection():
            logger.warning("No se pudo conectar a la base de datos")
        
        # 5. Verificar servicios
        try:
            auth_service = get_auth_service()
            file_service = get_file_service()
            analysis_service = get_cv_analysis_service()
            logger.info("Servicios inicializados correctamente")
        except Exception as e:
            logger.error(f"Error inicializando servicios: {e}")
            raise
        
        # 6. Verificar configuración de APIs de IA
        ai_warnings = []
        if not config.ai.openai_api_key:
            ai_warnings.append("OpenAI API key no configurada")
        if not config.ai.anthropic_api_key:
            ai_warnings.append("Anthropic API key no configurada")
        if not config.ai.gemini_api_key:
            ai_warnings.append("Gemini API key no configurada")
        
        if ai_warnings:
            logger.warning("APIs de IA no configuradas: " + ", ".join(ai_warnings))
        
        # 7. Registrar rutas
        web_routes = WebRoutes(app)
        logger.info("Rutas web registradas")
        
        # 8. Configurar manejo de errores
        @app.errorhandler(404)
        def not_found(error):
            return "Página no encontrada", 404
        
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Error interno: {error}")
            return "Error interno del servidor", 500
        
        # 9. Filtros de template
        @app.template_filter('datetime')
        def datetime_filter(value):
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            return value.strftime('%d/%m/%Y %H:%M') if value else ''
        
        logger.info("Aplicación inicializada correctamente")
        return app
        
    except Exception as e:
        print(f"Error crítico al inicializar la aplicación: {e}")
        raise

def init_database():
    """Comando CLI para inicializar la base de datos"""
    try:
        db_service = get_db_service()
        db_service.init_database()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")

def test_ai_apis():
    """Comando CLI para probar las APIs de IA"""
    config = get_config()
    
    print("🧪 Probando APIs de IA...")
    
    # Probar OpenAI
    if config.ai.openai_api_key:
        try:
            import openai
            openai.api_key = config.ai.openai_api_key
            print("✅ OpenAI API configurada")
        except Exception as e:
            print(f"❌ Error con OpenAI API: {e}")
    else:
        print("⚠️ OpenAI API key no configurada")
    
    # Probar Anthropic
    if config.ai.anthropic_api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.ai.anthropic_api_key)
            print("✅ Anthropic API configurada")
        except Exception as e:
            print(f"❌ Error con Anthropic API: {e}")
    else:
        print("⚠️ Anthropic API key no configurada")
    
    # Probar Gemini
    if config.ai.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.ai.gemini_api_key)
            print("✅ Gemini API configurada")
        except Exception as e:
            print(f"❌ Error con Gemini API: {e}")
    else:
        print("⚠️ Gemini API key no configurada")

def create_admin_user():
    """Comando CLI para crear usuario administrador"""
    try:
        auth_service = get_auth_service()
        
        email = input("Email del administrador: ")
        password = input("Contraseña: ")
        name = input("Nombre completo: ")
        
        result = auth_service.register_user(email, password, name)
        if result['success']:
            print(f"✅ Usuario administrador creado: {email}")
        else:
            print(f"❌ Error: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error creando usuario administrador: {e}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init-db':
            init_database()
        elif command == 'test-ai':
            test_ai_apis()
        elif command == 'create-admin':
            create_admin_user()
        else:
            print("Comandos disponibles:")
            print("  init-db      - Inicializar base de datos")
            print("  test-ai      - Probar APIs de IA")
            print("  create-admin - Crear usuario administrador")
    else:
        # Ejecutar aplicación
        app = create_app()
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )