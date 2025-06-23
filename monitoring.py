"""Sistema de Monitoreo y Métricas para ARMind"""

import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from collections import defaultdict, deque
import threading
import json

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Recolector de métricas del sistema"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)
        self.lock = threading.Lock()
        
        # Mantener solo las últimas 1000 métricas por tipo
        self.max_metrics = 1000
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Incrementar contador"""
        with self.lock:
            key = self._build_key(name, tags)
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Establecer valor de gauge"""
        with self.lock:
            key = self._build_key(name, tags)
            self.gauges[key] = value
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Registrar tiempo de ejecución"""
        with self.lock:
            key = self._build_key(name, tags)
            self.timers[key].append({
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            # Mantener solo las últimas métricas
            if len(self.timers[key]) > self.max_metrics:
                self.timers[key] = self.timers[key][-self.max_metrics:]
    
    def _build_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Construir clave única para métrica"""
        if not tags:
            return name
        
        tag_str = ','.join([f"{k}={v}" for k, v in sorted(tags.items())])
        return f"{name}[{tag_str}]"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        with self.lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'timers': {}
            }
            
            # Calcular estadísticas de timers
            for key, times in self.timers.items():
                if times:
                    durations = [t['duration'] for t in times]
                    summary['timers'][key] = {
                        'count': len(durations),
                        'avg': sum(durations) / len(durations),
                        'min': min(durations),
                        'max': max(durations),
                        'recent': times[-10:]  # Últimas 10 mediciones
                    }
            
            return summary

class SystemMonitor:
    """Monitor del sistema"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 30):
        """Iniciar monitoreo del sistema"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"✅ Monitoreo del sistema iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Detener monitoreo del sistema"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Monitoreo del sistema detenido")
    
    def _monitor_loop(self, interval: int):
        """Loop principal de monitoreo"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error en monitoreo del sistema: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Recolectar métricas del sistema"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.set_gauge('system.cpu.usage', cpu_percent)
        
        # Memoria
        memory = psutil.virtual_memory()
        self.metrics.set_gauge('system.memory.usage', memory.percent)
        self.metrics.set_gauge('system.memory.available', memory.available)
        self.metrics.set_gauge('system.memory.used', memory.used)
        
        # Disco
        disk = psutil.disk_usage('/')
        self.metrics.set_gauge('system.disk.usage', disk.percent)
        self.metrics.set_gauge('system.disk.free', disk.free)
        
        # Procesos
        process_count = len(psutil.pids())
        self.metrics.set_gauge('system.processes.count', process_count)
        
        # Red (si está disponible)
        try:
            net_io = psutil.net_io_counters()
            self.metrics.set_gauge('system.network.bytes_sent', net_io.bytes_sent)
            self.metrics.set_gauge('system.network.bytes_recv', net_io.bytes_recv)
        except Exception:
            pass

class ApplicationMonitor:
    """Monitor de la aplicación"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registrar request HTTP"""
        self.total_requests += 1
        
        # Métricas de request
        tags = {
            'method': method,
            'endpoint': endpoint,
            'status': str(status_code)
        }
        
        self.metrics.increment_counter('http.requests.total', tags=tags)
        self.metrics.record_timer('http.request.duration', duration, tags=tags)
        
        # Registrar errores
        if status_code >= 400:
            self.error_count += 1
            self.metrics.increment_counter('http.errors.total', tags=tags)
        
        # Mantener historial de tiempos de respuesta
        self.request_times.append({
            'timestamp': datetime.now(),
            'duration': duration,
            'status': status_code
        })
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        if not self.request_times:
            return {}
        
        recent_requests = [r for r in self.request_times 
                          if datetime.now() - r['timestamp'] < timedelta(minutes=5)]
        
        if not recent_requests:
            return {}
        
        durations = [r['duration'] for r in recent_requests]
        error_rate = len([r for r in recent_requests if r['status'] >= 400]) / len(recent_requests)
        
        return {
            'requests_per_minute': len(recent_requests),
            'avg_response_time': sum(durations) / len(durations),
            'error_rate': error_rate * 100,
            'total_requests': self.total_requests,
            'total_errors': self.error_count
        }

def monitor_performance(operation_name: str):
    """Decorador para monitorear rendimiento de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Registrar métrica exitosa
                from flask import current_app
                if hasattr(current_app, 'metrics_collector'):
                    current_app.metrics_collector.record_timer(
                        f'operation.{operation_name}.duration',
                        duration,
                        tags={'status': 'success'}
                    )
                    current_app.metrics_collector.increment_counter(
                        f'operation.{operation_name}.total',
                        tags={'status': 'success'}
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Registrar métrica de error
                from flask import current_app
                if hasattr(current_app, 'metrics_collector'):
                    current_app.metrics_collector.record_timer(
                        f'operation.{operation_name}.duration',
                        duration,
                        tags={'status': 'error'}
                    )
                    current_app.metrics_collector.increment_counter(
                        f'operation.{operation_name}.total',
                        tags={'status': 'error'}
                    )
                
                raise
        
        return wrapper
    return decorator

class HealthChecker:
    """Verificador de salud del sistema"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func, critical: bool = False):
        """Registrar verificación de salud"""
        self.checks[name] = {
            'func': check_func,
            'critical': critical
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Ejecutar todas las verificaciones de salud"""
        results = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        overall_healthy = True
        
        for name, check in self.checks.items():
            try:
                start_time = time.time()
                check_result = check['func']()
                duration = time.time() - start_time
                
                is_healthy = check_result.get('healthy', True)
                
                results['checks'][name] = {
                    'healthy': is_healthy,
                    'duration': duration,
                    'message': check_result.get('message', 'OK'),
                    'critical': check['critical']
                }
                
                if not is_healthy and check['critical']:
                    overall_healthy = False
                    
            except Exception as e:
                results['checks'][name] = {
                    'healthy': False,
                    'error': str(e),
                    'critical': check['critical']
                }
                
                if check['critical']:
                    overall_healthy = False
        
        results['status'] = 'healthy' if overall_healthy else 'unhealthy'
        return results

def init_monitoring(app):
    """Inicializar sistema de monitoreo"""
    # Crear componentes de monitoreo
    metrics_collector = MetricsCollector()
    system_monitor = SystemMonitor(metrics_collector)
    app_monitor = ApplicationMonitor(metrics_collector)
    health_checker = HealthChecker()
    
    # Registrar en la aplicación
    app.metrics_collector = metrics_collector
    app.system_monitor = system_monitor
    app.app_monitor = app_monitor
    app.health_checker = health_checker
    
    # Registrar verificaciones básicas de salud
    def check_database():
        try:
            # Aquí iría la verificación de la base de datos
            return {'healthy': True, 'message': 'Database connection OK'}
        except Exception as e:
            return {'healthy': False, 'message': f'Database error: {e}'}
    
    def check_redis():
        try:
            if hasattr(app, 'cache_service') and app.cache_service.available:
                app.cache_service.redis_client.ping()
                return {'healthy': True, 'message': 'Redis connection OK'}
            else:
                return {'healthy': False, 'message': 'Redis not available'}
        except Exception as e:
            return {'healthy': False, 'message': f'Redis error: {e}'}
    
    health_checker.register_check('database', check_database, critical=True)
    health_checker.register_check('redis', check_redis, critical=False)
    
    # Iniciar monitoreo del sistema
    system_monitor.start_monitoring()
    
    logger.info("✅ Sistema de monitoreo inicializado")
    
    return {
        'metrics_collector': metrics_collector,
        'system_monitor': system_monitor,
        'app_monitor': app_monitor,
        'health_checker': health_checker
    }