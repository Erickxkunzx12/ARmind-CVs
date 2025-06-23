"""Factory de Aplicación ARMind con Servicios Integrados"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from typing import Optional

# Importar configuraciones y servicios
from enhanced_config import init_config, get_config
from cache_service import init_cache
from monitoring import init_monitoring
from logging_config import setup_logging, log_request_middleware

def create_app(environment: str = None) -> Flask:
    """Factory para crear la aplicación Flask con todos los servicios"""
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Inicializar configuración
    config = init_config(environment)
    app.config.update(config.flask_config)
    
    # Configurar CORS
    CORS(app, origins=['http://localhost:3000', 'http://localhost:5000'])
    
    # Configurar logging
    logging_components = setup_logging({
        'LOG_LEVEL': config.monitoring.log_level,
        'LOG_FORMAT': config.monitoring.log_format,
        'LOG_DIR': config.monitoring.log_dir
    })
    
    app.security_logger = logging_components['security_logger']
    app.app_logger = logging_components['app_logger']
    
    # Configurar middleware de logging
    log_request_middleware(app)
    
    # Inicializar cache
    if config.cache.enabled:
        cache_service = init_cache(app)
        app.logger.info("✅ Servicio de cache inicializado")
    else:
        app.logger.info("⚠️ Cache deshabilitado")
    
    # Inicializar monitoreo
    if config.monitoring.enabled:
        monitoring_components = init_monitoring(app)
        app.logger.info("✅ Sistema de monitoreo inicializado")
    else:
        app.logger.info("⚠️ Monitoreo deshabilitado")
    
    # Registrar blueprints y rutas
    register_blueprints(app)
    register_error_handlers(app)
    register_health_endpoints(app)
    register_metrics_endpoints(app)
    
    # Configurar hooks de aplicación
    setup_app_hooks(app)
    
    app.logger.info(f"Aplicacion ARMind creada correctamente (entorno: {config.environment})")
    
    return app

def register_blueprints(app: Flask):
    """Registrar blueprints de la aplicación"""
    
    # Importar y registrar blueprints existentes
    try:
        # Aquí se importarían los blueprints existentes del proyecto
        # from routes import main_bp, auth_bp, api_bp
        # app.register_blueprint(main_bp)
        # app.register_blueprint(auth_bp, url_prefix='/auth')
        # app.register_blueprint(api_bp, url_prefix='/api')
        
        # Por ahora, crear rutas básicas
        @app.route('/')
        def index():
            return jsonify({
                'message': 'ARMind CV Analyzer API',
                'version': '2.0.0',
                'status': 'running',
                'environment': get_config().environment
            })
        
        @app.route('/api/status')
        def api_status():
            config = get_config()
            return jsonify({
                'status': 'healthy',
                'services': {
                    'cache': config.cache.enabled and hasattr(app, 'cache_service'),
                    'monitoring': config.monitoring.enabled and hasattr(app, 'metrics_collector'),
                    'database': bool(config.database.password),
                    'ai': len(config.ai.available_providers) > 0
                },
                'config_summary': config.get_summary()
            })
        
        app.logger.info("✅ Rutas básicas registradas")
        
    except ImportError as e:
        app.logger.warning(f"⚠️ No se pudieron importar algunos blueprints: {e}")

def register_error_handlers(app: Flask):
    """Registrar manejadores de errores"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid',
            'status_code': 400
        }), 400
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429
        }), 429
    
    app.logger.info("✅ Manejadores de errores registrados")

def register_health_endpoints(app: Flask):
    """Registrar endpoints de salud"""
    
    @app.route('/health')
    def health_check():
        """Endpoint básico de salud"""
        return jsonify({
            'status': 'healthy',
            'timestamp': app.config.get('START_TIME', 'unknown')
        })
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Endpoint detallado de salud"""
        if hasattr(app, 'health_checker'):
            return jsonify(app.health_checker.run_health_checks())
        else:
            return jsonify({
                'status': 'healthy',
                'message': 'Health checker not available'
            })
    
    @app.route('/health/ready')
    def readiness_check():
        """Endpoint de readiness para Kubernetes"""
        config = get_config()
        
        # Verificar servicios críticos
        ready = True
        services = {}
        
        # Verificar base de datos
        try:
            # Aquí iría la verificación real de la base de datos
            services['database'] = 'ready'
        except Exception as e:
            services['database'] = f'not ready: {e}'
            ready = False
        
        # Verificar cache si está habilitado
        if config.cache.enabled and hasattr(app, 'cache_service'):
            if app.cache_service.available:
                services['cache'] = 'ready'
            else:
                services['cache'] = 'not ready'
                # Cache no es crítico, no afecta readiness
        
        status_code = 200 if ready else 503
        return jsonify({
            'status': 'ready' if ready else 'not ready',
            'services': services
        }), status_code
    
    app.logger.info("Endpoints de salud registrados correctamente")

def register_metrics_endpoints(app: Flask):
    """Registrar endpoints de métricas"""
    
    @app.route('/metrics')
    def metrics():
        """Endpoint de métricas para Prometheus"""
        if not hasattr(app, 'metrics_collector'):
            return "Metrics not available", 404
        
        metrics_data = app.metrics_collector.get_metrics_summary()
        
        # Formato simple para Prometheus (se puede mejorar)
        output = []
        
        # Contadores
        for name, value in metrics_data.get('counters', {}).items():
            output.append(f"# TYPE {name} counter")
            output.append(f"{name} {value}")
        
        # Gauges
        for name, value in metrics_data.get('gauges', {}).items():
            output.append(f"# TYPE {name} gauge")
            output.append(f"{name} {value}")
        
        return "\n".join(output), 200, {'Content-Type': 'text/plain'}
    
    @app.route('/metrics/json')
    def metrics_json():
        """Endpoint de métricas en formato JSON"""
        if not hasattr(app, 'metrics_collector'):
            return jsonify({'error': 'Metrics not available'}), 404
        
        metrics_data = app.metrics_collector.get_metrics_summary()
        
        # Agregar métricas de rendimiento de la aplicación
        if hasattr(app, 'app_monitor'):
            performance_metrics = app.app_monitor.get_performance_metrics()
            metrics_data['performance'] = performance_metrics
        
        # Agregar estadísticas de cache
        if hasattr(app, 'cache_service'):
            cache_stats = app.cache_service.get_cache_stats()
            metrics_data['cache'] = cache_stats
        
        return jsonify(metrics_data)
    
    app.logger.info("Endpoints de metricas registrados correctamente")

def setup_app_hooks(app: Flask):
    """Configurar hooks de la aplicación"""
    
    # Usar record_once en lugar de before_first_request (deprecado en Flask 2.2+)
    def initialize_app():
        """Inicializar aplicación"""
        if not hasattr(app, '_initialized'):
            import time
            app.config['START_TIME'] = time.time()
            app.logger.info("Aplicacion inicializada correctamente")
            app._initialized = True
    
    # Llamar inicialización inmediatamente
    initialize_app()
    
    @app.teardown_appcontext
    def teardown_db(error):
        """Limpiar contexto de base de datos"""
        # Aquí iría la limpieza de conexiones de base de datos
        pass
    
    # Configurar límites de rate limiting si está disponible
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[get_config().performance.api_rate_limit]
        )
        
        app.limiter = limiter
        app.logger.info("✅ Rate limiting configurado")
        
    except ImportError:
        app.logger.warning("⚠️ Flask-Limiter no disponible, rate limiting deshabilitado")
    
    app.logger.info("✅ Hooks de aplicación configurados")

def create_production_app() -> Flask:
    """Crear aplicación para producción"""
    return create_app('production')

def create_development_app() -> Flask:
    """Crear aplicación para desarrollo"""
    return create_app('development')

def create_testing_app() -> Flask:
    """Crear aplicación para testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

if __name__ == '__main__':
    # Crear y ejecutar aplicación en modo desarrollo
    app = create_development_app()
    
    # Configurar servidor de desarrollo
    config = get_config()
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=config.debug,
        threaded=True
    )